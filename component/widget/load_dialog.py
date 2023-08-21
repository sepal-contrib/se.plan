import json

import geopandas as gpd
from ipyleaflet import GeoJSON
from sepal_ui import color as sc
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component.message import cm
from component.widget.base_dialog import BaseDialog


class LoadDialog(BaseDialog):
    def __init__(self, map_):
        super().__init__(class_="mb-5 mt-2")

        self.map_ = map_

        # add a btn to click
        self.btn = sw.Btn(
            cm.map.shapes.btn, icon="mdi-download", class_="ml-2", small=True
        )
        btn_cancel = sw.Btn(cm.map.dialog.drawing.cancel, small=True)

        # and the vector selector
        self.w_vector = CustomVector(label=cm.map.shapes.file)

        # create an alert for the su.loading_button
        self.alert = sw.Alert()

        # generate the panels
        title = sw.CardTitle(children=[cm.map.shapes.title])
        text = sw.CardText(children=[self.w_vector, self.alert])
        actions = sw.CardActions(children=[sw.Spacer(), self.btn, btn_cancel])

        self.children = [sw.Card(children=[title, text, actions])]

        btn_cancel.on_event("click", self.close_dialog)

        self.btn.on_event("click", self._load_shapes)

    @su.loading_button(debug=False)
    def read_data(self):
        # extract information for compacity
        value = self.w_vector.v_model["value"]
        column = self.w_vector.v_model["column"]
        pathname = self.w_vector.v_model["pathname"]

        if column in ["ALL", None]:
            raise Exception("Please select data")

        # create the gdf and filter if necessary
        gdf = gpd.read_file(pathname)
        gdf = gdf if value is None else gdf[gdf[column] == value]

        return gdf, column

    def _load_shapes(self, widget, event, data):
        # get the data from the selected file
        gdf, column = self.load_shape.read_data()

        gdf = gdf.filter(items=[column, "geometry"])

        # add them to the map
        for i, row in gdf.iterrows():
            # transform the data into a feature
            feat = {
                "type": "Feature",
                "properties": {"style": {}},
                "geometry": row.geometry.__geo_interface__,
            }
            self._add_geom(feat, row[column])

        # display a tmp geometry before validation
        data = json.loads(gdf.to_json())
        style = {
            **cp.aoi_style,
            "color": sc.info,
            "fillColor": sc.info,
            "opacity": 0.5,
            "weight": 2,
        }
        layer = GeoJSON(data=data, style=style, name="tmp")
        self.map_.add_layer(layer)

        return


class CustomVector(sw.VectorField):
    def _update_file(self, change):
        """remove the select 'all feature' option as feature is used to name the AOIs."""

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.w_column.v_model = None
            self.w_column.items = None

        super()._update_file(change)

        # update the columns
        self.w_column.v_model = None
        self.w_column.items = self.w_column.items[1:]

        return self
