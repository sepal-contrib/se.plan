"""Custom dialog to display individual layers from questionnaire tile."""

import asyncio
from typing import Any, Literal, Optional, Union

import ee
from component.scripts.gee import create_layer
import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts.gee_task import GEETask
from sepal_ui.frontend.resize_trigger import rt
from sepal_ui.mapping import SepalMap
import sepal_ui.scripts.decorator as sd
from sepal_ui.mapping import InspectorControl
from sepal_ui.scripts.gee_interface import GEEInterface


from component import parameter as cp
from component.message import cm
from component.widget.base_dialog import BaseDialog, MapDialog
from component.widget.buttons import TextBtn
from component.widget.legend import Legend


class CustomInspectorControl(InspectorControl):

    def close_menu(self, *_):
        """Close the menu contet."""
        self.menu.v_model = False

    def open_menu(self, *_):
        """Open the menu content."""
        self.menu.v_model = True


class PreviewMapDialog(MapDialog):

    def __init__(self, gee_interface: GEEInterface, theme_toggle=None):
        super().__init__(max_width="950px", min_width="950px")

        self._tasks: dict[str, GEETask] = {}

        self.gee_interface = gee_interface
        self.map_ = SepalMap(theme_toggle=theme_toggle, gee_interface=gee_interface)
        self.map_.layout.height = "60vw"
        self.map_.layout.height = "60vh"
        self.retain_focus = False  # To prevent on focus ipyvuetify error
        self.legend = Legend()
        self.map_.add(self.legend)
        self.map_.min_zoom = 1
        self.inspector_control = CustomInspectorControl(self.map_, position="topright")
        self.map_.add(self.inspector_control)

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

        self.children = [self.map_card]

        self.btn_close.on_event("click", self.close_dialog)

    def close_dialog(self, *_):
        """Closes the dialog."""

        for task in self._tasks.values():
            task.cancel()

        # Close the inspector control
        self.inspector_control.close_menu()

        super().close_dialog()

    def open_dialog(self):
        """Opens the dialog and creates a resize event."""
        super().open_dialog()

    async def get_maps(self, aoi, ee_map, base_layer, vis_params, type_):
        """Returns the map and the legend."""

        coros = [
            self.gee_interface.get_map_id_async(aoi),
            self.gee_interface.get_info_async(aoi.bounds().coordinates().get(0)),
            self.gee_interface.get_map_id_async(ee_map.clip(aoi), vis_params),
        ]

        if base_layer:
            coros.append(self.gee_interface.get_map_id_async(base_layer.clip(aoi)))
        else:
            coros.append(asyncio.sleep(0, result=None))

        aoi_id, boundaries, layer_id, base_id = await asyncio.gather(
            *coros, return_exceptions=True
        )

        return aoi_id, boundaries, layer_id, base_id

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

        self.map_.remove_all()
        self.open_dialog()
        self.title.children = [name]
        self.map_card.loading = True

        def maps_callback(_):
            aoi_map_id, coords, layer_map_id, base_layer_map_id = self._tasks[
                "maps"
            ].result
            self.map_.zoom_bounds((*coords[0], *coords[2]))
            self.map_.add_layer(create_layer(aoi_map_id, "AOI"))
            if base_layer_map_id:
                self.map_.add_layer(create_layer(base_layer_map_id, "Base Layer", True))
            self.map_.add_layer(create_layer(layer_map_id, name, True))

        self._tasks["maps"] = self.gee_interface.create_task(
            func=self.get_maps,
            key="add_preview_maps",
            on_done=maps_callback,
            on_error=lambda x: None,
            on_finally=lambda: setattr(self.map_card, "loading", False),
        )

        def min_max_callback(_):
            if self._tasks["minmax"]:
                min_, max_ = self._tasks["minmax"].result

                self.legend.update_legend(
                    "gradient",
                    "legend",
                    [min_, max_],
                    map_vis["palette"],
                )
                vis_params = map_vis.copy()
                vis_params.update(min=min_, max=max_)

            self._tasks["maps"].start(aoi, layer, base_layer, vis_params, type_)

        self._tasks["minmax"] = self.gee_interface.create_task(
            func=self.get_min_max,
            key="layer_minmax",
            on_done=min_max_callback,
            on_error=lambda x: None,
            on_finally=lambda: setattr(self.map_card, "loading", False),
        )

        legend_type = "gradient" if type_ in ["benefit", "cost"] else "binary"
        map_vis = cp.map_vis[legend_type]

        if type_ == "constraint":
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

        if type_ in ["benefit", "cost"]:
            self._tasks["minmax"].start(layer, aoi)
            return

        self._tasks["maps"].start(aoi, layer, base_layer, vis_params, type_)

    async def get_min_max(self, image, geometry):
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

        values = await self.gee_interface.get_info_async(min_max)
        max_, min_ = [round(val, 2) for val in values.values()]

        min_ = 0 if not min_ else min_
        max_ = 1 if not max_ else max_

        return min_, max_
