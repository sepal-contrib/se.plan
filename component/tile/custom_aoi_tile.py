import ee
import pandas as pd
import pkg_resources
import sepal_ui.sepalwidgets as sw
from ipyleaflet import WidgetControl
from sepal_ui.mapping import SepalMap

import component.parameter as cp
from component.message import cm
from component.model.recipe import Recipe
from component.widget.alert_state import AlertState
from component.widget.custom_aoi_view import SeplanAoiView

ee.Initialize()


class AoiTile(sw.Layout):
    """Overwrite the map of the tile to replace it with a customMap."""

    def __init__(self):
        self.class_ = "d-block custom_map"
        self._metadata = {"mount_id": "aoi_tile"}

        super().__init__()

    def build(self, recipe: Recipe, build_alert: AlertState):
        """Build the custom aoi tile."""
        build_alert.set_state("new", "aoi", "building")

        self.map_ = SepalMap(gee=True)
        self.map_.dc.hide()
        self.map_.min_zoom = 3
        self.map_.add_basemap("SATELLITE")

        # Build the aoi view with our custom aoi_model
        self.view = SeplanAoiView(model=recipe.seplan_aoi, map_=self.map_)

        aoi_control = WidgetControl(
            widget=self.view, position="topleft", transparent_bg=True
        )

        self.map_.add(aoi_control)
        self.children = [self.map_]

        # bind an extra js behaviour
        self.view.observe(self._check_lmic, "updated")

        build_alert.set_state("new", "aoi", "done")

    def _check_lmic(self, _):
        """Every time a new aoi is set check if it fits the LMIC country list."""
        # check over the lmic country number
        if self.view.model.admin:
            code = self.view.model.admin

            # get the country code out of the admin one (that can be level 1 or 2)

            # Access to the parquet file in the package data (required with sepal_ui>2.16.4)
            resource_path = "data/gaul_database.parquet"
            content = pkg_resources.resource_filename("pygaul", resource_path)

            df = pd.read_parquet(content).astype(str)
            level_0_code = df[
                (df.ADM0_CODE == code) | (df.ADM1_CODE == code) | (df.ADM2_CODE == code)
            ].ADM0_CODE.iloc[0]

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
            included = ee.Algorithms.IsEqual(
                bit_test.getNumber("constant"), 2
            ).getInfo()

        included or self.view.alert.add_msg(cm.aoi.not_lmic, "warning")

        return self
