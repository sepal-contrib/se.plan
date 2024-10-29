"""Custom dialog to display individual layers from questionnaire tile."""

from typing import Literal

import ee
import sepal_ui.sepalwidgets as sw
from sepal_ui.frontend.resize_trigger import rt
from sepal_ui.mapping import SepalMap
import sepal_ui.scripts.decorator as sd


from component import parameter as cp
from component.message import cm
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn
from component.widget.legend import Legend


class PreviewMapDialog(BaseDialog):
    def __init__(self, solara_basemap_tiles: dict = None):
        super().__init__(max_width="950px", min_width="950px")

        self.map_ = SepalMap(solara_basemap_tiles=solara_basemap_tiles)
        self.map_.layout.height = "60vw"
        self.map_.layout.height = "60vh"
        self.retain_focus = False  # To prevent on focus ipyvuetify error

        self.rt = rt

        self.legend = Legend()
        self.map_.add(self.legend)
        self.map_.min_zoom = 1

        self.title = sw.CardTitle()
        self.btn_close = TextBtn(cm.questionnaire.map.close)

        self.map_card = sw.Card(
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

        self.children = [
            # self.rt,
            self.map_card,
        ]

        self.btn_close.on_event("click", self.close_dialog)

    def open_dialog(self):
        """Opens the dialog and creates a resize event."""
        super().open_dialog()
        self.rt.resize()

    @sd.switch("loading", on_widgets=["map_card"])
    def show_layer(
        self,
        layer: ee.Image,
        type_: Literal["benefit", "constraint", "cost"],
        name: str,
        aoi: ee.FeatureCollection,
        base_layer: ee.Image = None,
    ) -> None:
        """Adds given layer to the map and opens the dialog.

        Args:
            layer (ee.Image): the image to display
            type_ (str): the type of the layer
            name (str): the name of the layer
            aoi (ee.FeatureCollection): the area of interest
            base_layer (ee.Image, optional): the base layer without mask. Defaults to None.
        """
        if not aoi:
            raise Exception(cm.questionnaire.error.no_aoi_on_map)

        self.map_.addLayer(aoi, {}, "AOI")
        self.map_.centerObject(aoi)
        self.map_.remove_all()

        self.open_dialog()
        self.title.children = [name]

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
            if base_layer:
                layer = layer.clip(aoi)
                self.map_.addLayer(
                    base_layer.clip(aoi), {}, "base_layer", use_map_vis=False
                )

        self.map_.addLayer(layer.clip(aoi), vis_params, "layer")

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
            reducer=ee.Reducer.minMax(),
            geometry=geometry,
            scale=1,
            maxPixels=1e5,
            bestEffort=True,
            tileScale=16,
        )
        max_, min_ = [round(val, 2) for val in min_max.getInfo().values()]

        min_ = 0 if not min_ else min_
        max_ = 1 if not max_ else max_

        return min_, max_
