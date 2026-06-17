
import logging

import ee
import pandas as pd
import pygaul
import sepal_ui.sepalwidgets as sw
from sepal_ui.mapping import SepalMap
from sepal_ui.scripts.gee_interface import GEEInterface
from sepal_ui.scripts.utils import init_ee

import component.parameter as cp
from component.message import cm
from component.model.recipe import Recipe
from component.scripts.aoi_geometry import _aoi_bbox
from component.widget.custom_aoi_view import SeplanAoiView

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
        # Reset the soft-warning flag; only the partial / unverifiable verdicts
        # below (or the async GEE path) raise it again.
        seplan_aoi.aoi_lmic_warning = False
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
        """Treat GEE check failures as 'unverifiable' — warn but allow.

        A failed heuristic shouldn't lock the user out, so the AOI stays usable
        (``aoi_lmic_valid`` True) with a visible notice and ``aoi_lmic_warning``
        set so the step dialog stays open. Bumping the counter releases any
        waiters (e.g. the dialog-close observer).
        """
        logger.warning(f"LMIC check failed: {exc}")
        self.view.alert.add_msg(cm.aoi.lmic_check_failed, "error")
        self.seplan_aoi.aoi_lmic_valid = True
        self.seplan_aoi.aoi_lmic_warning = True
        self.seplan_aoi.aoi_lmic_checked += 1

    async def _check_lmic_gee_async(self):
        """Async, tiered LMIC coverage check for non-admin AOIs.

        Computes the fraction of the AOI that falls on LMIC land and grades it:
        ``>= cp.MIN_LMIC_COVERAGE`` passes cleanly; a smaller but non-zero share
        is allowed with a warning (``aoi_lmic_warning``); a zero share is
        blocked. This replaces an earlier ``bitwiseAnd`` test that required
        *every* pixel to be LMIC — at 1 km a handful of coastline pixels (e.g.
        ~10 of ~1.9M for Indonesia, 99.999% LMIC) collapsed the AND to 0 and
        falsely flagged whole LMIC countries as out of scope.

        Drives ``get_info_async`` on the GEE event loop. Safe to launch from
        either the kernel thread or the GEE thread.
        """
        seplan_aoi = self.seplan_aoi
        lmic_raster = ee.Image(
            "projects/john-ee-282116/assets/fao-restoration/misc/lmic_global_1k"
        )
        fc = seplan_aoi.feature_collection

        # select(0)+rename so the verdict doesn't depend on the asset's band
        # name. Keep the raster MASKED (no unmask): masked ocean/no-data is
        # excluded, so ``fraction`` is the LMIC share of the AOI's land pixels.
        # Clip to the AOI + reduce over its bbox rather than geometry=fc.geometry(),
        # which would dissolve the whole collection and blow the 2M-edge limit on
        # a large non-admin AOI (e.g. an uploaded dense boundary).
        lmic01 = lmic_raster.select(0).rename("lmic")
        masked = lmic01.clip(fc)
        fraction = masked.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=_aoi_bbox(fc),
            scale=1000,
            bestEffort=True,
            maxPixels=1e13,
        ).getNumber("lmic")

        # ``If(fraction, ...)`` guards against a null mean (AOI outside the
        # raster footprint) so we always get a number back.
        frac = await self.gee_interface.get_info_async(
            ee.Number(ee.Algorithms.If(fraction, fraction, 0))
        )
        self._apply_lmic_verdict(frac)

    def _apply_lmic_verdict(self, frac) -> None:
        """Grade an LMIC land-coverage fraction into a verdict + user alert.

        ``frac`` is the share (0..1) of the AOI that falls on LMIC land:
        ``>= cp.MIN_LMIC_COVERAGE`` passes cleanly; a smaller non-zero share is
        allowed but warned (``aoi_lmic_warning`` keeps the step dialog open so
        the notice is read); zero/None is blocked as fully out of scope.
        Pure-Python and synchronous so it can be unit-tested without GEE.
        """
        seplan_aoi = self.seplan_aoi
        frac = frac or 0.0
        if frac <= 0:
            # entirely out of scope → hard block.
            self.view.alert.add_msg(cm.aoi.not_lmic, "warning")
            seplan_aoi.aoi_lmic_valid = False
            seplan_aoi.aoi_lmic_warning = False
        elif frac < cp.MIN_LMIC_COVERAGE:
            # partial coverage → allow, but warn and keep the dialog open.
            self.view.alert.add_msg(
                cm.aoi.partial_lmic.format(round(frac * 100)), "warning"
            )
            seplan_aoi.aoi_lmic_valid = True
            seplan_aoi.aoi_lmic_warning = True
        else:
            # majority LMIC → clean pass.
            seplan_aoi.aoi_lmic_valid = True
            seplan_aoi.aoi_lmic_warning = False
        seplan_aoi.aoi_lmic_checked += 1
