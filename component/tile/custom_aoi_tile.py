from typing import Union

import ee
import pandas as pd
import pygaul
from component.frontend.icons import icon
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import IconBtn, TextBtn
import sepal_ui.sepalwidgets as sw
from ipyleaflet import WidgetControl
from sepal_ui.mapping import SepalMap
from sepal_ui.scripts.gee_interface import GEEInterface

import component.parameter as cp
from component.message import cm
from component.model.recipe import Recipe
from component.widget.custom_aoi_view import SeplanAoiView

from sepal_ui.scripts.utils import init_ee
import logging

logger = logging.getLogger("SEPLAN")

init_ee()


class AoiView(sw.Layout):
    """Overwrite the map of the tile to replace it with a customMap."""

    def __init__(
        self,
        map_: SepalMap,
        gee_interface: GEEInterface = None,
        recipe: Recipe = None,
        app_model=None,
    ):
        if not recipe:
            recipe = Recipe()
        self.class_ = "d-block aoi_map"
        self._metadata = {"mount_id": "aoi_tile"}
        self.gee_interface = gee_interface
        self.map_ = map_
        # Keep the wrapper reference — ``SeplanAoiView.model`` is the inner
        # ``AoiModel`` (set via super().__init__), so the LMIC traits live
        # on this object instead.
        self.seplan_aoi = recipe.seplan_aoi

        super().__init__()

        # Build the aoi view with our custom aoi_model
        self.view = SeplanAoiView(
            model=recipe.seplan_aoi,
            map_=self.map_,
            gee_interface=gee_interface,
            app_model=app_model,
        )

        self.children = [self.view]

        self.view.observe(self._check_lmic, "updated")

    def _check_lmic(self, _):
        """Every time a new aoi is set check if it fits the LMIC country list.

        The admin branch is pure-Python (pygaul + a CSV read) and runs inline.
        The DRAW/SHAPE branch needs GEE, so it's dispatched as a background
        task — this keeps the observer safe to fire from any thread (notably
        from inside ``SeplanAoiView._auto_submit_async`` which already runs on
        the GEE event loop and would deadlock on a sync ``get_info`` call).

        Writes the verdict to ``seplan_aoi.aoi_lmic_valid`` and bumps
        ``aoi_lmic_checked`` so dialog-close gating and right-panel
        action-blocking can react.
        """
        seplan_aoi = self.seplan_aoi  # SeplanAoi wrapper
        if self.view.model.admin:
            logger.info("Checking if the aoi is in the LMIC country list")
            code = str(self.view.model.admin)

            # Resolve the admin code (level 0, 1, or 2) to its ISO3 country code
            # via pygaul. Match on ISO3 instead of GAUL numeric codes because
            # pygaul 0.4+ uses GAUL 2024 codes that differ from the old codes
            # stored in the LMIC CSV.
            df = pygaul._df().astype(str)

            iso3_code = df[
                (df["gaul0_code"] == code)
                | (df["gaul1_code"] == code)
                | (df["gaul2_code"] == code)
            ]["iso3_code"].iloc[0]

            lmic_iso3 = pd.read_csv(cp.country_list).ISO3.astype(str)
            included = bool((lmic_iso3 == iso3_code).any())
            if not included:
                self.view.alert.add_msg(cm.aoi.not_lmic, "warning")
            seplan_aoi.aoi_lmic_valid = included
            seplan_aoi.aoi_lmic_checked += 1
            return self

        # Non-admin (DRAW / SHAPE / ASSET) — flip valid=False optimistically
        # while the async GEE check runs. This blocks the dialog auto-close
        # and the right-panel actions until a verdict lands; on success we
        # set valid=True before bumping ``aoi_lmic_checked`` so the close
        # observer sees the right value.
        seplan_aoi.aoi_lmic_valid = False
        task = self.gee_interface.create_task(
            func=self._check_lmic_gee_async,
            key="lmic_check_gee",
            on_error=self._on_gee_lmic_error,
        )
        self._lmic_task = task  # keep ref so it isn't garbage-collected
        task.start()
        return self

    def _on_gee_lmic_error(self, exc: Exception):
        """Treat GEE check failures as 'unknown' — leave aoi_lmic_valid False.

        The user can still see the warning (logged here) but the right-panel
        actions stay disabled until a successful re-check. Bumping the
        counter releases any waiters (e.g. the dialog-close observer).
        """
        logger.warning(f"LMIC check failed: {exc}")
        self.seplan_aoi.aoi_lmic_checked += 1

    async def _check_lmic_gee_async(self):
        """Async LMIC overlap check for non-admin AOIs.

        Drives ``get_info_async`` on the GEE event loop. Safe to launch from
        either the kernel thread or the GEE thread.
        """
        seplan_aoi = self.seplan_aoi
        lmic_raster = ee.Image(
            "projects/john-ee-282116/assets/fao-restoration/misc/lmic_global_1k"
        )
        aoi_ee_geom = seplan_aoi.feature_collection.geometry()

        empt = ee.Image().byte()
        aoi_ee_raster = empt.paint(aoi_ee_geom, 1)

        bit_test = aoi_ee_raster.add(lmic_raster).reduceRegion(
            reducer=ee.Reducer.bitwiseAnd(),
            geometry=aoi_ee_geom,
            scale=1000,
            bestEffort=True,
            maxPixels=1e13,
        )
        # bitwiseAnd == 2 means full LMIC coverage (1 partial, 0 none).
        included = bool(
            await self.gee_interface.get_info_async(
                ee.Algorithms.IsEqual(bit_test.getNumber("constant"), 2),
            )
        )
        if not included:
            self.view.alert.add_msg(cm.aoi.not_lmic, "warning")
        seplan_aoi.aoi_lmic_valid = included
        seplan_aoi.aoi_lmic_checked += 1
