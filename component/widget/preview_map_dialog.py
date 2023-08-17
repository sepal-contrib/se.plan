"""Custom dialog to display individual layers from questionnaire tile."""
from typing import Literal

import ee
import sepal_ui.sepalwidgets as sw
from ipyleaflet import Map

from component.message import cm
from component.widget.base_dialog import BaseDialog


class PreviewMapDialog(BaseDialog):
    def __init__(self):
        self.map_ = Map()
        self.btn_close = sw.Btn(cm.questionnaire.map, class_="mr-2")

        self.children = [
            sw.CardText(
                children=[
                    self.map_,
                ]
            ),
            sw.CardActions(children=[sw.Spacer(), self.btn_close]),
        ]

    def add_layer(
        self, layer: ee.Image, type_: Literal["benefit", "constraint", "cost"]
    ) -> None:
        """Adds given layer to the map and opens the dialog."""
        self.map_.addLayer(layer, {}, "layer")
        self.set_legend(type_)
        self.open()

    def add_weighted_benefit(self, layer: ee.Image):
        """Adds given layer to the map and opens the dialog."""
        self.map_.addLayer(layer, {}, "weighted_benefit")
        self.open()

    def add_costs(self, layer: ee.Image):
        """Adds normalized cost layer."""
        self.map_.addLayer(layer, {}, "costs")
        self.open()
