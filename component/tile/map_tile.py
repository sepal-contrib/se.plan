from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component.model.app_model import AppModel
from component.model.recipe import Recipe
from component.widget.alert_state import Alert, AlertDialog, AlertState
from component.widget.map import SeplanMap
from component.widget.map_toolbar import MapToolbar
from component.message import cm


class MapTile(sw.Layout):
    def __init__(self, recipe: Recipe, app_model: AppModel = None):
        """Define the map tile layout.

        Args:
            app_model (AppModel, optional): The app model, it is used to comunicate this
                map_tile with the app (like opening the info dialog when the map_tile drawer is clicked). Defaults to None.
        """
        self._metadata = {"mount_id": "map_tile"}
        self.class_ = "d-block custom_map"
        self.app_model = app_model

        super().__init__()

        self.recipe = recipe
        self.colors = []
        self.alert = Alert()
        alert_dialog = AlertDialog(self.alert)

        self.map_ = SeplanMap(recipe.seplan_aoi)
        self.map_toolbar = MapToolbar(
            recipe=self.recipe, map_=self.map_, alert=self.alert
        )

        # init the final layers
        self.wlc_outputs = None
        self.area_dashboard = None
        self.theme_dashboard = None

        self.children = [
            alert_dialog,
            self.map_toolbar,
            self.map_,
        ]

        # decorate compute indicator and dashboard
        self._compute = su.loading_button(self.alert, self.map_toolbar.btn_compute)(
            self._compute
        )

        # # add js behaviour
        self.map_toolbar.btn_compute.on_event("click", self._compute)

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

    def _compute(self, *_):
        """Compute the restoration plan and display the map."""

        aoi = self.recipe.seplan_aoi.feature_collection

        benefit_index = self.recipe.seplan.get_benefit_index(clip=True)
        benefit_cost_index = (
            self.recipe.seplan.get_benefit_cost_index(clip=True).multiply(4).add(1)
        )

        constraint_index = self.recipe.seplan.get_constraint_index().unmask(0).clip(aoi)

        self.map_.centerObject(aoi, zoom_out=3)
        self.map_.add_ee_layer(
            benefit_index, cp.layer_vis, cm.layer.index.benefit_index.name
        )
        self.map_.add_ee_layer(
            benefit_cost_index, cp.layer_vis, cm.layer.index.benefit_cost_index.name
        )
        self.map_.add_ee_layer(
            constraint_index, cp.layer_vis, cm.layer.index.constraint_index.name
        )
