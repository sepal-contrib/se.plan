from sepal_ui import mapping as sm
from sepal_ui import aoi
from sepal_ui.scripts import decorator as sd
from sepal_ui.message import ms
from sepal_ui import sepalwidgets as sw
import ee
from ipyleaflet import TileLayer

from component import new_model as cmod
from component import parameter as cp
from component import new_scripts as cs


class IndexLayerRow(sm.LayerRow):
    """custom layer_row to remove the prefix from the layer names"""

    def __init__(self, prefix: str, layer: TileLayer):

        super().__init__(layer)
        display_name = self.children[0].children[0].replace(prefix, "")
        self.children[0].children = [display_name]


class IndexLayersControl(sm.LayersControl):
    """show all the layers Index and update each time a new one is added"""

    _prefix = "[index]"

    def __init__(self, m: sm.SepalMap, **kwargs):

        # save the map
        self.map = m

        super().__init__(m, **kwargs)

        # change the btn
        self.menu.v_slots[0]["children"].children[0] = "IND"

    def update_table(self, *args) -> None:
        """silence this method"""
        pass

    @sd.need_ee
    def update_index(self) -> None:
        """Update the table content."""

        layers = [ly for ly in self.map.layers if ly.name.startswith("[index]")]

        # create a table of layerLine
        layer_rows = []
        if len(layers) > 0:
            head = [sm.HeaderRow(ms.layer_control.layer.header)]
            rows = [IndexLayerRow(self._prefix, ly) for ly in reversed(layers)]
            layer_rows = head + rows

        # create a table from these rows and wrap it in the radioGroup
        tbody = sw.Html(tag="tbody", children=layer_rows)
        table = sw.SimpleTable(children=[tbody], dense=True, class_="v-no-border")

        # set the table as children of the widget
        self.tile.children = [table]
