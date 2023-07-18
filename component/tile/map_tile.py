from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component import scripts as cs
from component.scripts.seplan import Seplan
from component.widget.map import SeplanMap
from component.widget.map_toolbar import MapToolbar


class MapTile(sw.Layout):
    def __init__(self, seplan_model: Seplan, area_tile, theme_tile):
        self.attributes = {"_metadata": "map_widget"}
        self.class_ = "d-block"

        super().__init__()

        self.seplan_model = seplan_model
        self.colors = []
        self.alert = sw.Alert()
        self.map_ = SeplanMap()
        self.map_toolbar = MapToolbar(model=self.seplan_model, map_=self.map_)

        # get the dashboard tile
        self.area_tile = area_tile
        self.theme_tile = theme_tile

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
        benefit_index = (
            self.seplan_model.get_benefit_index(clip=True).multiply(4).add(1)
        )
        benefit_cost_index = (
            self.seplan_model.get_benefit_cost_index(clip=True).multiply(4).add(1)
        )
        constraint_index = (
            self.seplan_model.get_constraint_index(clip=True).multiply(4).add(1)
        )

        self.map_.add_ee_layer(benefit_index, cp.final_viz, "benefit index")
        self.map_.add_ee_layer(benefit_cost_index, cp.final_viz, "benefit_cost index")
        self.map_.add_ee_layer(constraint_index, cp.final_viz, "constraint_index")

        # enable the dashboard computation
        self.map_toolbar.btn_dashboard.disabled = False

    def _dashboard(self, widget, data, event):
        # handle the drawing features, affect them with a color an display them on the map as layers
        self._save_features()

        # create a name list
        names = [self.aoi_model.name] + [
            feat["properties"]["name"] for feat in self.draw_features["features"]
        ]

        # retreive the area and theme json result
        self.area_dashboard, self.theme_dashboard = cs.get_stats(
            self.wlc_outputs,
            self.layer_model,
            self.aoi_model,
            self.draw_features,
            names,
        )

        # save the dashboard as a csv
        cs.export_as_csv(
            self.area_dashboard,
            self.theme_dashboard,
            self.aoi_model.name,
            self.question_model.recipe_name,
        )

        # set the content of the panels
        self.theme_tile.dev_set_summary(self.theme_dashboard, names, self.colors)
        self.area_tile.set_summary(self.area_dashboard)

        return self
