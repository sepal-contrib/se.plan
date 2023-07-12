from copy import deepcopy

import ipyvuetify as v
import sepal_ui.sepalwidgets as sw
from ipyleaflet import WidgetControl, basemap_to_tiles, basemaps
from sepal_ui import mapping as sm

from component import parameter as cp
from component.message import cm


class SeplanMap(sm.SepalMap):
    EMPTY_FEATURES = {"type": "FeatureCollection", "features": []}

    def __init__(self, *args, **kwargs):
        self.attributes = {"id": "map"}
        self.dc = True
        self.vinspector = True

        super().__init__(*args, **kwargs)

        self.dc.hide()
        self.add_basemap("SATELLITE")
        self.draw_features = deepcopy(self.EMPTY_FEATURES)

        # create the map
        self.add(sm.FullScreenControl(self, position="topright"))
        self.add_colorbar(
            colors=cp.red_to_green, vmin=1, vmax=5, layer_name=cm.map.legend.title
        )

        # create a window to display AOI information
        self.html = sw.Html(tag="h3", style_="margin:0em 2em 0em 2em;")
        control = WidgetControl(widget=self.html, position="bottomright")
        self.add(control)

        # add cartoDB layer after everything to make sure it stays on top
        # workaround of https://github.com/jupyter-widgets/ipyleaflet/issues/452
        default = "Positron" if v.theme.dark is False else "DarkMatter"
        carto = basemap_to_tiles(basemaps.CartoDB[default])
        carto.base = True
        self.add_layer(carto)

        self.dc.on_draw(self._handle_draw)
        # self.name_dialog.observe(self.save_draw, "value")

    def _add_geom(self, geo_json, name):
        geo_json["properties"]["name"] = name
        self.draw_features["features"].append(geo_json)

        return self

    def save_draw(self, change):
        """save the geojson after the click on the button with it's custom name."""
        if change["new"] is True:
            return self

        self._add_geom(self.name_dialog.feature, self.name_dialog.w_name.v_model)

        return self

    def _display_name(self, feature, **kwargs):
        """update the AOI in the html viewver widget."""
        # if the feature is a aoi it has no name so I display only the sub AOI name
        # it will be solved with: https://github.com/12rambau/sepal_ui/issues/390
        name = (
            feature["properties"]["name"]
            if "name" in feature["properties"]
            else "Main AOI"
        )
        self.html.children = [name]

        return self

    def _handle_draw(self, target, action, geo_json):
        """handle the draw on map event."""
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
