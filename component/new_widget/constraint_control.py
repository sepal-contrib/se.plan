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


class ConstraintLayerRow(sm.LayerRow):
    """custom layer_row to remove the prefix from the layer names"""

    def __init__(self, prefix: str, layer: TileLayer):

        super().__init__(layer)
        display_name = self.children[0].children[0].replace(prefix, "")
        self.children[0].children = [display_name]


class ConstraintLayersControl(sm.LayersControl):
    """show all the layers from priorities and update each time a new one is added"""

    _prefix = "[constraint]"

    def __init__(
        self,
        m: sm.SepalMap,
        aoi_model: aoi.AoiModel,
        model: cmod.ConstraintModel,
        **kwargs
    ):

        # save the models
        self.aoi_model = aoi_model
        self.model = model

        super().__init__(m, **kwargs)

        # change the btn
        self.menu.v_slots[0]["children"].children[0] = "CON"

        # add an update method to force the layers when priorities are updated
        self.model.observe(self.update_costs, "validated")
        self.aoi_model.observe(self.update_costs, "name")

    def update_table(self, *args) -> None:
        """silence this method"""
        pass

    @sd.need_ee
    def update_costs(self, *args) -> None:
        """Update the table content."""

        # exit if aoi is not set
        if self.aoi_model.feature_collection is None:
            return

        # remove all the priority layers
        for layer in self.m.layers:
            if layer.name.startswith(self._prefix):
                self.m.remove_layer(layer)

        # create the layers and store them in a list
        layers = []
        for i, name in enumerate(self.model.names):
            aoi = self.aoi_model.feature_collection
            dataset = ee.Image(self.model.assets[i]).select(0).clip(aoi)
            red = ee.Reducer.minMax()
            min_max = (
                dataset.reduceRegion(reducer=red, geometry=aoi, scale=500)
                .toArray()
                .getInfo()
            )
            viz = {**cp.plt_viz["viridis"], "min": min(min_max), "max": max(min_max)}
            layer = cs.get_layer(dataset, viz, self._prefix + name, False)
            self.m.add_layer(layer)
            layers.append(layer)

        # create a table of layerLine
        layer_rows = []
        if len(layers) > 0:
            head = [sm.HeaderRow(ms.layer_control.layer.header)]
            rows = [ConstraintLayerRow(self._prefix, ly) for ly in reversed(layers)]
            layer_rows = head + rows

        # create a table from these rows and wrap it in the radioGroup
        tbody = sw.Html(tag="tbody", children=layer_rows)
        table = sw.SimpleTable(children=[tbody], dense=True, class_="v-no-border")

        # set the table as children of the widget
        self.tile.children = [table]
