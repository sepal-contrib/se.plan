from sepal_ui import aoi
from sepal_ui.message import ms
import pandas as pd
import ee
import ipyvuetify as v
from sepal_ui import sepalwidgets as sw

from component import parameter as cp
from component.message import cm
from component.widget.custom_map import CustomMap

ee.Initialize()


class CustomAoiTile(aoi.AoiTile):
    """
    overwrite the map of the tile to replace it with a customMap
    """

    def __init__(self, methods="ALL", gee=True, **kwargs):

        # create the map
        self.map = CustomMap(dc=True, gee=gee)
        self.map.dc.hide()

        # create the view
        # the view include the model
        self.view = aoi.AoiView(methods=methods, map_=self.map, gee=gee, **kwargs)
        self.view.elevation = 0

        # organise them in a layout
        layout = v.Layout(
            row=True,
            xs12=True,
            children=[
                v.Flex(xs12=True, md6=True, class_="pa-5", children=[self.view]),
                v.Flex(xs12=True, md6=True, class_="pa-1", children=[self.map]),
            ],
        )

        # create the tile
        sw.Tile.__init__(
            self, id_="aoi_tile", title=ms.aoi_sel.title, inputs=[layout], **kwargs
        )

        # bind an extra js behaviour
        self.view.observe(self._check_lmic, "updated")

    def _check_lmic(self, change):
        """Every time a new aoi is set check if it fits the LMIC country list"""

        # check over the lmic country number
        if self.view.model.admin:

            code = self.view.model.admin

            # get the country code out of the admin one (that can be level 1 or 2)
            df = pd.read_csv(self.view.model.FILE[1])
            level_0_code = df[
                (df.ADM0_CODE == code) | (df.ADM1_CODE == code) | (df.ADM2_CODE == code)
            ].ADM0_CODE.iloc[0]

            # read the country file
            country_codes = pd.read_csv(cp.country_list).GAUL
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
