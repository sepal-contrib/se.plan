import solara
from ipyleaflet import Map, TileLayer
from sepal_ui.mapping.basemaps import basemap_tiles


import ipyleaflet
import ipyvuetify as v
from sepal_ui.mapping import SepalMap


class MyMap(SepalMap):
    def __init__(self):
        super().__init__(scroll_wheel_zoom=True, center=(48.85, 2.35), zoom=12)

        btn = v.Btn(children=["add layer"])
        btn.on_event("click", self._add_layer)

        self.layers = [
            basemap_tiles["ROADMAP"],
            TileLayer(
                attribution="Google",
                base=False,
                max_zoom=22,
                name="Google Maps",
                options=[
                    "attribution",
                    "bounds",
                    "detect_retina",
                    "max_native_zoom",
                    "max_zoom",
                    "min_native_zoom",
                    "min_zoom",
                    "no_wrap",
                    "tile_size",
                    "tms",
                    "zoom_offset",
                ],
                url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            ),
        ]
        # Add layers control to the map
        self.add(ipyleaflet.LayersControl(position="topright"))

        self.add_control(ipyleaflet.WidgetControl(widget=btn, position="topright"))

    def _add_layer(self, *args):
        # layer = eval(str(basemap_tiles["TERRAIN"]))
        # # print(layer)

        # self.add_layer(layer)
        # layer = eval(str(basemap_tiles["ROADMAP"]))
        # print(layer)
        # self.add_layer(layer)

        layer = TileLayer(
            attribution="Google",
            base=False,
            max_zoom=22,
            name="Google Maps 2",
            options=[
                "attribution",
                "bounds",
                "detect_retina",
                "max_native_zoom",
                "max_zoom",
                "min_native_zoom",
                "min_zoom",
                "no_wrap",
                "tile_size",
                "tms",
                "zoom_offset",
            ],
            url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        )

        self.add_layer(layer)


@solara.component
def Page():
    solara_basemap_tiles = {k: eval(str(v)) for k, v in basemap_tiles.items()}
    SepalMap.element(solara_basemap_tiles=solara_basemap_tiles)
    # MyMap.element()
