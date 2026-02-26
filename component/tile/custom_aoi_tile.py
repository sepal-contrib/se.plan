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

            # get the country code out of the admin one (that can be level 1 or 2)
            # Follow pygaul issue #45 guidance: use the private dataframe accessor.
            df = pygaul._df().astype(str)

            if {"ADM0_CODE", "ADM1_CODE", "ADM2_CODE"}.issubset(df.columns):
                level_0_col, level_1_col, level_2_col = "ADM0_CODE", "ADM1_CODE", "ADM2_CODE"
            else:
                level_0_col, level_1_col, level_2_col = (
                    "gaul0_code",
                    "gaul1_code",
                    "gaul2_code",
                )

            level_0_code = df[
                (df[level_0_col] == code) | (df[level_1_col] == code) | (df[level_2_col] == code)
            ][level_0_col].iloc[0]

            # read the country file
            country_codes = pd.read_csv(cp.country_list).GAUL.astype(str)
            included = (country_codes == level_0_code).any()

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
