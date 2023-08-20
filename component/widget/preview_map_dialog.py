"""Custom dialog to display individual layers from questionnaire tile."""
from typing import Literal

import ee
import sepal_ui.sepalwidgets as sw
from sepal_ui.mapping import SepalMap

from component.widget.base_dialog import BaseDialog
from component.widget.custom_widgets import Legend


class PreviewMapDialog(BaseDialog):
    def __init__(self):
        super().__init__(max_width="950px", min_width="950px")
        self.map_ = SepalMap()

        self.title = sw.CardTitle()
        self.btn_close = sw.Btn("Close", class_="mr-2")

        self.children = [
            sw.Card(
                children=[
                    self.title,
                    sw.CardText(
                        children=[
                            self.map_,
                        ]
                    ),
                    sw.CardActions(children=[sw.Spacer(), self.btn_close]),
                ],
            )
        ]

        self.btn_close.on_event("click", self.close_dialog)

    def show_layer(
        self,
        layer: ee.Image,
        type_: Literal["benefit", "constraint", "cost"],
        name: str,
        aoi: ee.FeatureCollection,
    ) -> None:
        """Adds given layer to the map and opens the dialog."""
        self.map_.remove_layer("layer", none_ok=True)
        print(layer.name)
        self.open_dialog()
        self.title.children = [name]
        self.map_.zoom_ee_object(layer)
        self.map_.addLayer(layer.clip(aoi), {}, "layer")
        self.set_legend(type_)

    def set_legend(self, type_: Literal["benefit", "constraint", "cost"]):
        """Set legend based on type of layer."""
        return

        legend = Legend(type_)
        self.map_.add_control(legend, position="bottomright")

    def add_weighted_benefit(self, layer: ee.Image):
        """Adds given layer to the map and opens the dialog."""
        self.map_.addLayer(layer, {}, "weighted_benefit")
        self.open_dialog()

    def add_normalized_costs(self, layer: ee.Image):
        """Adds normalized cost layer."""
        self.map_.addLayer(layer, {}, "costs")
        self.open_dialog()

    def add_mask(self, layer: ee.Image):
        """Adds mask layer."""
        self.map_.addLayer(layer, {}, "mask")
        self.open_dialog()
