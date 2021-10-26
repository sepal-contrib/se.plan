from pathlib import Path

from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from sepal_ui.scripts import utils as su
import ipyvuetify as v
from shapely import geometry as sg
import geopandas as gpd
import geemap
import ee
import json
from ipyleaflet import WidgetControl
from ipyleaflet import GeoJSON
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex

from component.message import cm
from component import parameter as cp
from component import scripts as cs
from component import widget as cw


class MapTile(sw.Tile):
    def __init__(self, questionnaire_tile, aoi_model, area_tile, theme_tile):

        # add the explanation
        mkd = sw.Markdown("  \n".join(cm.map.txt))

        # create a save widget
        self.save = cw.ExportMap()

        # create the map
        self.m = sm.SepalMap(dc=True).hide_dc()
        self.m.add_control(WidgetControl(widget=self.save, position="topleft"))
        self.m.add_colorbar(colors=cp.red_to_green, vmin=0, vmax=5)

        # drawing managment
        self.draw_features = {"type": "FeatureCollection", "features": []}
        self.colors = []
        self.name_dialog = cw.CustomAoiDialog()

        # create a layout with 2 btn
        self.map_btn = sw.Btn(cm.compute.btn, class_="ma-2")
        self.compute_dashboard = sw.Btn(
            cm.map.compute_dashboard, class_="ma-2", disabled=True
        )

        # models
        self.layer_model = questionnaire_tile.layer_model
        self.question_model = questionnaire_tile.question_model
        self.aoi_model = aoi_model

        # create the shape loader
        self.load_shape = cw.LoadShapes()

        # get the dashboard tile
        self.area_tile = area_tile
        self.theme_tile = theme_tile

        # init the final layers
        self.wlc_outputs = None
        self.area_dashboard = None
        self.theme_dashboard = None

        # create the tile
        super().__init__(
            id_="map_widget",
            title=cm.map.title,
            inputs=[mkd, self.load_shape, self.m, self.name_dialog],
            alert=sw.Alert(),
            btn=v.Layout(children=[self.map_btn, self.compute_dashboard]),
        )

        # decorate the function
        self._compute = su.loading_button(self.alert, self.map_btn, debug=True)(
            self._compute
        )
        self._dashboard = su.loading_button(
            self.alert, self.compute_dashboard, debug=True
        )(self._dashboard)

        # add js behaviour
        self.compute_dashboard.on_event("click", self._dashboard)
        self.m.dc.on_draw(self._handle_draw)
        self.map_btn.on_event("click", self._compute)
        self.load_shape.btn.on_event("click", self._load_shapes)
        self.name_dialog.observe(self.save_draw, "value")

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

        return

    def _add_geom(self, geo_json, name):

        geo_json["properties"]["name"] = name
        self.draw_features["features"].append(geo_json)

        return self

    def _compute(self, widget, data, event):
        """compute the restoration plan and display the map"""

        # create a layer and a dashboard
        self.wlc_outputs = cs.wlc(
            self.layer_model.layer_list,
            self.question_model.constraints,
            self.question_model.priorities,
            self.aoi_model.feature_collection,
        )

        # display the layer in the map
        cs.display_layer(self.wlc_outputs[0], self.aoi_model, self.m)

        self.save.set_data(
            self.wlc_outputs[0],
            self.aoi_model.feature_collection.geometry(),
            self.question_model.recipe_name,
            self.aoi_model.name,
        )

        # add the possiblity to draw on the map and release the compute dashboard btn
        self.m.show_dc()

        # enable the dashboard computation
        self.compute_dashboard.disabled = False

        return self

    def _save_features(self):
        """save the features as layers on the map"""

        # remove any sub aoi layer
        [self.m.remove_layer(l) for l in self.m.layers if "sub aoi" in l.name]

        # save the drawn features
        draw_features = self.draw_features

        # remove the shapes from the dc
        # as a side effect the draw_feature member will be emptied
        self.m.dc.clear()

        # reset the draw_features
        self.draw_features = draw_features

        # set up the colors using the tab10 matplotlib colormap
        self.colors = [
            to_hex(plt.cm.tab10(i)) for i in range(len(self.draw_features["features"]))
        ]

        # create a layer for each aoi
        for feat, color in zip(self.draw_features["features"], self.colors):
            name = feat["properties"]["name"]
            style = {**cp.aoi_style, "color": color, "fillColor": color}
            layer = GeoJSON(data=feat, style=style, name=f"sub aoi {name}")
            self.m.add_layer(layer)

        return self

    def _dashboard(self, widget, data, event):

        # handle the drawing features, affect them with a color an display them on the map as layers
        self._save_features()

        # create a name list
        names = [self.aoi_model.name] + [
            feat["properties"]["name"] for feat in self.draw_features["features"]
        ]

        # retreive the area and theme json result
        self.area_dashboard, self.theme_dashboard = cs.get_stats(
            self.wlc_outputs,
            self.layer_model,
            self.aoi_model,
            self.draw_features,
            names,
        )

        self.theme_tile.dev_set_summary(self.theme_dashboard, names, self.colors)

        self.area_tile.set_summary(self.area_dashboard)

        return self

    def _handle_draw(self, target, action, geo_json):
        """handle the draw on map event"""

        # polygonize circles
        if "radius" in geo_json["properties"]["style"]:
            geo_json = self.polygonize(geo_json)

        if action == "created":  # no edit as you don't know which one to change

            # open the naming dialog (the popup will do the saving instead of this function)
            self.name_dialog.update_aoi(
                geo_json, len(self.draw_features["features"]) + 1
            )

        elif action == "deleted":

            for feat in self.draw_features["features"]:
                if feat["geometry"] == geo_json["geometry"]:
                    self.draw_features["features"].remove(feat)

        return self

    def save_draw(self, change):
        """save the geojson after the click on the button with it's custom name"""

        if change["new"] == True:
            return self

        self._add_geom(self.name_dialog.feature, self.name_dialog.w_name.v_model)

        return self

    @staticmethod
    def polygonize(geo_json):
        """
        Transform a ipyleaflet circle (a point with a radius) into a GeoJson multipolygon

        Params:
            geo_json (json): the circle geojson

        Return:
            (json): the polygonised circle
        """

        # get the input
        radius = geo_json["properties"]["style"]["radius"]
        coordinates = geo_json["geometry"]["coordinates"]

        # create shapely point
        circle = (
            gpd.GeoSeries([sg.Point(coordinates)], crs=4326)
            .to_crs(3857)
            .buffer(radius)
            .to_crs(4326)
        )

        # insert it in the geo_json
        json = geo_json
        json["geometry"] = circle[0].__geo_interface__

        return json
