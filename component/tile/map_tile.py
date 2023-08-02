from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component.model.aoi_model import SeplanAoi
from component.scripts.seplan import Seplan
from component.scripts.statistics import get_summary_statistics
from component.tile.dashboard_tile import OverallDashboard, ThemeDashboard
from component.widget.map import SeplanMap
from component.widget.map_toolbar import MapToolbar


class MapTile(sw.Layout):
    def __init__(
        self,
        seplan_model: Seplan,
        seplan_aoi: SeplanAoi,
        overall_dash: OverallDashboard = None,
        theme_dash: ThemeDashboard = None,
    ):
        self.attributes = {"_metadata": "map_widget"}
        self.class_ = "d-block"

        super().__init__()

        self.seplan_model = seplan_model
        self.colors = []
        self.alert = sw.Alert()
        self.map_ = SeplanMap(seplan_aoi)
        self.map_toolbar = MapToolbar(model=self.seplan_model, map_=self.map_)

        # get the dashboard tile
        self.overall_dash = overall_dash
        self.theme_dash = theme_dash

        # init the final layers
        self.wlc_outputs = None
        self.area_dashboard = None
        self.theme_dashboard = None

        self.children = [
            self.alert,
            self.map_toolbar,
            self.map_,
        ]

        # decorate compute indicator and dashboard
        self._compute = su.loading_button(
            self.alert, self.map_toolbar.btn_compute, debug=True
        )(self._compute)

        self._dashboard = su.loading_button(
            self.alert, self.map_toolbar.btn_dashboard, debug=True
        )(self._dashboard)

        # # add js behaviour
        self.map_toolbar.btn_compute.on_event("click", self._compute)
        self.map_toolbar.btn_dashboard.on_event("click", self._dashboard)

    def _compute(self, widget, data, event):
        """compute the restoration plan and display the map."""
        benefit_index = self.seplan_model.get_benefit_index(clip=True)
        benefit_cost_index = (
            self.seplan_model.get_benefit_cost_index(clip=True).multiply(4).add(1)
        )
        constraint_index = self.seplan_model.get_constraint_index(clip=True)

        self.map_.add_ee_layer(benefit_index, cp.final_viz, "benefit index")
        self.map_.add_ee_layer(benefit_cost_index, cp.final_viz, "benefit_cost index")
        self.map_.add_ee_layer(constraint_index, cp.final_viz, "constraint_index")

        # enable the dashboard computation
        self.map_toolbar.btn_dashboard.disabled = False

    def _dashboard(self, *_):
        """compute the restoration plan and display the map."""
        summary_stats = get_summary_statistics(self.seplan_model)

        # set the content of the panels
        self.overall_dash.set_summary(summary_stats)
        self.theme_dash.set_summary(summary_stats)

        # # save the dashboard as a csv
        # cs.export_as_csv(
        #     self.area_dashboard,
        #     self.theme_dashboard,
        #     self.aoi_model.name,
        #     self.question_model.recipe_name,
        # )
