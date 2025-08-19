import asyncio
from typing import Union

from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from sepal_ui.scripts.gee_interface import GEEInterface

from component.model.app_model import AppModel
from component.model.recipe import Recipe
from component.widget.alert_state import Alert, AlertDialog, AlertState
from component.widget.map import SeplanMap

import logging

log = logging.getLogger("SEPLAN.map_tile")


class MapTile(sw.Layout):
    def __init__(
        self,
        map_: SeplanMap,
        app_model: AppModel,
        recipe: Recipe,
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
        self.map_ = map_

        super().__init__()

        self.recipe = recipe
        self.colors = []
        self.alert = Alert()
        alert_dialog = AlertDialog(self.alert)

        self.gee_interface = gee_interface

        self.children = [
            alert_dialog,
        ]

        self.recipe.seplan_aoi.observe(self._update_aoi, "updated")

        # This will open the info dialog when the map_tile drawer is clicked
        if self.app_model:
            self.app_model.observe(self.open_info_dialog, "active_drawer")

        # Use reset_view trait ffrom seplan_aoi to reset the map view (remove all the layers)

        self.recipe.seplan_aoi.observe(lambda *_: self.map_.remove_all(), "reset_view")

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
