import asyncio
from typing import Union

from component.scripts.gee import create_layer
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from sepal_ui.scripts.gee_interface import GEEInterface

from component import parameter as cp
from component.model.app_model import AppModel
from component.model.recipe import Recipe
from component.widget.alert_state import Alert, AlertDialog, AlertState
from component.widget.map import SeplanMap
from component.widget.map_toolbar import MapToolbar
from component.message import cm

from sepal_ui.scripts.gee_task import GEETask
from ipyleaflet import TileLayer

import logging

log = logging.getLogger("SEPLAN.map_tile")


class MapTile(sw.Layout):
    def __init__(
        self,
        app_model: AppModel,
        recipe: Recipe,
        theme_toggle: None,
        gee_interface: GEEInterface,
        sepal_session=None,
    ):
        """Define the map tile layout.

        Args:
            app_model (AppModel, optional): The app model, it is used to comunicate this
                map_tile with the app (like opening the info dialog when the map_tile drawer is clicked). Defaults to None.
        """
        self._metadata = {"mount_id": "map_tile"}
        self.class_ = "d-block results_map"
        self.app_model = app_model

        super().__init__()

        self.recipe = recipe
        self.colors = []
        self.alert = Alert()
        alert_dialog = AlertDialog(self.alert)

        self.gee_interface = gee_interface

        self.map_ = SeplanMap(
            recipe.seplan_aoi,
            theme_toggle=theme_toggle,
            gee_interface=gee_interface,
        )
        self.map_toolbar = MapToolbar(
            recipe=self.recipe,
            map_=self.map_,
            alert=self.alert,
            gee_interface=gee_interface,
            sepal_session=sepal_session,
        )

        self._configure_task_button()

        # init the final layers
        self.wlc_outputs = None
        self.area_dashboard = None
        self.theme_dashboard = None

        self.children = [
            alert_dialog,
            self.map_toolbar,
            self.map_,
        ]

        self.recipe.seplan_aoi.observe(self._update_aoi, "updated")

        # This will open the info dialog when the map_tile drawer is clicked
        if self.app_model:
            self.app_model.observe(self.open_info_dialog, "active_drawer")

        # Use reset_view trait ffrom seplan_aoi to reset the map view (remove all the layers)

        self.recipe.seplan_aoi.observe(lambda *_: self.map_.remove_all(), "reset_view")

    def _configure_task_button(self):
        """Configure the TaskButton instance with the task factory for computing all maps."""

        def create_compute_maps_task():
            def callback(result):
                task = self.map_toolbar.btn_compute._task
                if task:
                    bounds, map_id_dicts = task.result
                    log.debug(
                        f"All maps computed. Results: {len(map_id_dicts) if map_id_dicts else 0} maps"
                    )

                    self.map_.zoom_bounds((*bounds[0], *bounds[2]))

                    if map_id_dicts:
                        layer_names = [
                            cm.layer.index.benefit_index.name,
                            cm.layer.index.benefit_cost_index.name,
                            cm.layer.index.constraint_index.name,
                        ]

                        for i, map_id_dict in enumerate(map_id_dicts):
                            if isinstance(map_id_dict, Exception):
                                log.error(f"Error in task {i}: {map_id_dict}")
                                self.alert.add_msg(
                                    f"Failed to load {layer_names[i]}: {map_id_dict}",
                                    type_="error",
                                )
                                continue

                            log.debug(f"Adding layer {i}: {layer_names[i]}")
                            self.map_.add_layer(
                                create_layer(map_id_dict, layer_names[i])
                            )

            return self.gee_interface.create_task(
                func=self.get_maps,
                key="compute_all_maps",
                on_done=callback,
                on_error=lambda e: self.alert.add_msg(str(e), type_="error"),
            )

        self.map_toolbar.btn_compute.configure(
            task_factory=create_compute_maps_task,
            start_args=(),
        )

    def open_info_dialog(self, change):
        """Open the info dialog when the map_tile app drawer is clicked."""
        if change["new"] == "map_tile":
            self.map_toolbar.info_dialog.open_dialog()

            # I just want to open the dialog once, so I remove the observer
            self.app_model.unobserve(self.open_info_dialog, "active_drawer")

    def _update_aoi(self, *_):
        """Update the map when the aoi is updated."""
        aoi = self.recipe.seplan_aoi.feature_collection
        if aoi:
            self.map_.add_ee_layer(self.recipe.seplan_aoi.feature_collection, {}, "aoi")

    async def get_maps(self):

        aoi = self.recipe.seplan_aoi.feature_collection

        benefit_index = self.recipe.seplan.get_benefit_index(clip=True)
        benefit_cost_index = (
            self.recipe.seplan.get_benefit_cost_index(clip=True).multiply(4).add(1)
        )
        constraint_index = self.recipe.seplan.get_constraint_index().unmask(0).clip(aoi)

        tasks = [
            self.gee_interface.get_info_async(aoi.bounds().coordinates().get(0)),
            self.gee_interface.get_map_id_async(benefit_index, cp.layer_vis),
            self.gee_interface.get_map_id_async(benefit_cost_index, cp.layer_vis),
            self.gee_interface.get_map_id_async(constraint_index, cp.layer_vis),
        ]

        bounds, benef_idx_id, cost_idx_id, const_id = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        return bounds, (benef_idx_id, cost_idx_id, const_id)
