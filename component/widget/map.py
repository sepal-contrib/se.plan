from copy import deepcopy

import ipyvuetify as v
import sepal_ui.sepalwidgets as sw
from ipyleaflet import GeoJSON, WidgetControl, basemap_to_tiles, basemaps
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex
from sepal_ui import mapping as sm
from traitlets import Dict, Int, directional_link

from component import parameter as cp
from component.message import cm
from component.model.aoi_model import SeplanAoi


class SeplanMap(sm.SepalMap):
    custom_layers = Dict({"type": "FeatureCollection", "features": []}).tag(sync=True)
    "dict: custom geometries drawn by the user"

    new_geom = Int(0).tag(sync=True)
    """int: either a new geometry has been drawn on the map"""

    def __init__(self, seplan_aoi: SeplanAoi, *args, **kwargs):
        self.aoi_model = seplan_aoi

        self.attributes = {"id": "map"}
        self.dc = True
        self.vinspector = True

        super().__init__(*args, **kwargs)

        self.dc.hide()
        self.add_basemap("SATELLITE")

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
        self.observe(self.on_custom_layers, "custom_layers")

        directional_link((self, "custom_layers"), (seplan_aoi, "custom_layers"))

    def on_custom_layers(self, *_):
        """Add custom layers to the map."""
        geojson_layers = [layer for layer in self.layers if isinstance(layer, GeoJSON)]
        # Check if there are new geometries in the custom_layers
        # If there are new geometries that are not in the map, add them

        colors = [
            to_hex(plt.cm.tab10(i)) for i in range(len(self.custom_layers["features"]))
        ]

        # Add layers to the map
        for i, feat in enumerate(self.custom_layers["features"]):
            if feat["properties"]["name"] not in [lyr.name for lyr in geojson_layers]:
                # Add the layer to the map
                style = {**cp.aoi_style, "color": colors[i], "fillColor": colors[i]}
                hover_style = {**style, "fillOpacity": 0.4, "weight": 2}
                layer = GeoJSON(
                    data=feat,
                    style=style,
                    hover_style=hover_style,
                    name=feat["properties"]["name"],
                )
                layer.on_hover(self._display_name)

                # Add the layer to the map_layers list
                self.add(layer)

        # Remove layers from the map
        for layer in geojson_layers:
            if layer.name not in [
                feat["properties"]["name"] for feat in self.custom_layers["features"]
            ]:
                self.remove_layer(layer)

    def remove_custom_layer(self, layer_id):
        """Remove custom layer from the custom_layers dict."""
        # Create a copy of the current custom_layers dict
        current_feats = deepcopy(self.custom_layers)

        # Search the layer_id in the custom_layers dict
        for feat in current_feats["features"]:
            if feat["properties"]["id"] == layer_id:
                current_feats["features"].remove(feat)

                # Trigger the change in the custom_layers dict
                self.custom_layers = current_feats

    def _handle_draw(self, target, action, geo_json):
        """handle the draw on map event."""
        # polygonize circles
        if "radius" in geo_json["properties"]["style"]:
            geo_json = self.to_json()

        if action == "created":
            # save_geom_dialog will be listening to this trait
            self.new_geom += 1

        elif action == "deleted":
            current_feats = deepcopy(self.custom_layers)
            for feat in current_feats["features"]:
                if feat["geometry"] == geo_json["geometry"]:
                    current_feats["features"].remove(feat)

                    # Trigger the change in the custom_layers dict
                    self.custom_layers = current_feats

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
