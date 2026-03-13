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
    ):
        if not recipe:
            recipe = Recipe()
        self.class_ = "d-block aoi_map"
        self._metadata = {"mount_id": "aoi_tile"}
        self.gee_interface = gee_interface
        self.map_ = map_

        super().__init__()

        # Build the aoi view with our custom aoi_model
        self.view = SeplanAoiView(
            model=recipe.seplan_aoi, map_=self.map_, gee_interface=gee_interface
        )

        self.children = [self.view]

        self.view.observe(self._check_lmic, "updated")

    def _check_lmic(self, _):
        """Every time a new aoi is set check if it fits the LMIC country list."""
        # check over the lmic country number
        if self.view.model.admin:
            logger.info(f"Checking if the aoi is in the LMIC country list")
            code = str(self.view.model.admin)

            # Resolve the admin code (level 0, 1, or 2) to its ISO3 country code
            # via pygaul. Match on ISO3 instead of GAUL numeric codes because
            # pygaul 0.4+ uses GAUL 2024 codes that differ from the old codes
            # stored in the LMIC CSV.
            df = pygaul._df().astype(str)

            if {"ADM0_CODE", "ADM1_CODE", "ADM2_CODE"}.issubset(df.columns):
                level_0_col, level_1_col, level_2_col = "ADM0_CODE", "ADM1_CODE", "ADM2_CODE"
                iso3_col = "ISO3_CODE" if "ISO3_CODE" in df.columns else "iso3_code"
            else:
                level_0_col, level_1_col, level_2_col = (
                    "gaul0_code",
                    "gaul1_code",
                    "gaul2_code",
                )
                iso3_col = "iso3_code"

            iso3_code = df[
                (df[level_0_col] == code) | (df[level_1_col] == code) | (df[level_2_col] == code)
            ][iso3_col].iloc[0]

            # read the country file and match by ISO3
            lmic_iso3 = pd.read_csv(cp.country_list).ISO3.astype(str)
            included = (lmic_iso3 == iso3_code).any()

        # check if the aoi is in the LMIC
        else:
            lmic_raster = ee.Image(
                "projects/john-ee-282116/assets/fao-restoration/misc/lmic_global_1k"
            )

            aoi_ee_geom = self.view.model.feature_collection.geometry()

            empt = ee.Image().byte()
            aoi_ee_raster = empt.paint(aoi_ee_geom, 1)

            bit_test = aoi_ee_raster.add(lmic_raster).reduceRegion(
                reducer=ee.Reducer.bitwiseAnd(),
                geometry=aoi_ee_geom,
                scale=1000,
                bestEffort=True,
                maxPixels=1e13,
            )
            # test if bitwiseAnd is 2 (1 is partial coverage, 0 no coverage)
            included = self.gee_interface.get_info(
                ee.Algorithms.IsEqual(bit_test.getNumber("constant"), 2),
            )

        included or self.view.alert.add_msg(cm.aoi.not_lmic, "warning")
        return self
