"""Custom dialog to display individual layers from questionnaire tile."""
from typing import Literal

import ee
import sepal_ui.sepalwidgets as sw
from sepal_ui.frontend.resize_trigger import rt
from sepal_ui.mapping import SepalMap

from component import parameter as cp
from component.message import cm
from component.widget.base_dialog import BaseDialog
from component.widget.legend import Legend


class PreviewMapDialog(BaseDialog):
    def __init__(self):
        super().__init__(max_width="950px", min_width="950px")

        self.map_ = SepalMap()
        self.rt = rt

        self.legend = Legend()
        self.map_.add(self.legend)

        self.title = sw.CardTitle()
        self.btn_close = sw.Btn(cm.questionnaire.map.close, class_="mr-2")

        self.children = [
            self.rt,
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
            ),
        ]

        self.btn_close.on_event("click", self.close_dialog)

    def open_dialog(self):
        """Opens the dialog and creates a resize event."""
        super().open_dialog()
        self.rt.resize()

    def show_layer(
        self,
        layer: ee.Image,
        type_: Literal["benefit", "constraint", "cost"],
        name: str,
        aoi: ee.FeatureCollection,
    ) -> None:
        """Adds given layer to the map and opens the dialog."""
        if not aoi:
            raise Exception(cm.questionnaire.error.no_aoi_on_map)

        self.map_.centerObject(aoi, zoom_out=3)
        self.map_.remove_layer("layer", none_ok=True)

        self.open_dialog()
        self.title.children = [name]
        self.map_.addLayer(aoi, {}, "AOI")

        legend_type = "gradient" if type_ in ["benefit", "cost"] else "binary"

        map_vis = cp.map_vis[legend_type]

        if type_ in ["benefit", "cost"]:
            min_, max_ = self.get_min_max(layer, aoi)
            self.legend.update_legend(
                "gradient",
                "legend",
                [min_, max_],
                map_vis["palette"],
            )
            vis_params = map_vis.copy()
            vis_params.update(min=min_, max=max_)

        elif type_ == "constraint":
            self.legend.update_legend(
                "stepped",
                "legend",
                map_vis["names"],
                map_vis["palette"],
            )
            vis_params = map_vis.copy()
            vis_params.update(min=0, max=1)
            layer = layer.unmask(0)

        self.map_.addLayer(layer.clip(aoi), vis_params, "layer")

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

    def get_min_max(self, image, geometry):
        """Display the image on the map.

        Args:
            image (str): the asset name of the image
            geometry (ee.Geometry): the geometry of the AOI

        """
        # clip image
        ee_image = image.clip(geometry)

        # get minmax
        min_max = ee_image.reduceRegion(
            reducer=ee.Reducer.minMax(), geometry=geometry, scale=10000, bestEffort=True
        )
        max_, min_ = min_max.getInfo().values()

        min_ = 0 if not min_ else min_
        max_ = 1 if not max_ else max_

        return min_, max_
