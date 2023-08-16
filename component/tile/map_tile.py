from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component.model.recipe import Recipe
from component.widget.alert_state import Alert, AlertDialog, AlertState
from component.widget.map import SeplanMap
from component.widget.map_toolbar import MapToolbar


class MapTile(sw.Layout):
    def __init__(self):
        self._metadata = {"mount_id": "map_tile"}
        self.class_ = "d-block"

        super().__init__()

    def build(
        self,
        recipe: Recipe,
        build_alert: AlertState,
    ):
        build_alert.set_state("new", "map", "building")

        self.recipe = recipe
        self.colors = []
        self.alert = Alert()
        alert_dialog = AlertDialog(self.alert)

        self.map_ = SeplanMap(recipe.seplan_aoi)
        self.map_toolbar = MapToolbar(model=self.recipe.seplan, map_=self.map_)

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
        self._compute = su.loading_button(
            self.alert, self.map_toolbar.btn_compute, debug=True
        )(self._compute)

        # # add js behaviour
        self.map_toolbar.btn_compute.on_event("click", self._compute)

        build_alert.set_state("new", "map", "done")

        self.recipe.seplan_aoi.aoi_model.observe(self._update_aoi, "updated")

    def _update_aoi(self, *_):
        """Update the map when the aoi is updated."""
        aoi = self.recipe.seplan_aoi.feature_collection
        if aoi:
            self.map_.add_ee_layer(self.recipe.seplan_aoi.feature_collection, {}, "aoi")

    def _compute(self, *_):
        """Compute the restoration plan and display the map."""
        benefit_index = self.recipe.seplan.get_benefit_index(clip=True)
        benefit_cost_index = (
            self.recipe.seplan.get_benefit_cost_index(clip=True).multiply(4).add(1)
        )
        constraint_index = self.recipe.seplan.get_constraint_index(clip=True)

        self.map_.add_ee_layer(benefit_index, cp.final_viz, "benefit index")
        self.map_.add_ee_layer(benefit_cost_index, cp.final_viz, "benefit_cost index")
        self.map_.add_ee_layer(constraint_index, cp.final_viz, "constraint_index")
