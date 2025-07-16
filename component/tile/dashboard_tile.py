from typing import List, Tuple, Union
from component.types import (
    BenefitChartsData,
    ConstraintChartsData,
    CostChartData,
    MeanStatsDict,
    RecipeStatsDict,
)

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from sepal_ui.scripts.gee_interface import GEEInterface

from component import widget as cw
from component.message import cm
from component.model.recipe import Recipe
from component.parameter.vis_params import PLOT_COLORS
from component.scripts.compute import export_as_csv
from component.scripts.plots import (
    get_bars_chart,
    get_suitability_charts,
    parse_layer_data,
)
from component.scripts.seplan import Seplan
from component.scripts.statistics import get_summary_statistics_async
from component.widget.alert_state import Alert, AlertDialog
from component.widget.suitability_table import get_summary_table
from component.widget.custom_widgets import DashToolbar
from component.widget.dashboard_layer_panels import LayerFull, LayerPercentage
import logging

logger = logging.getLogger("SEPLAN")


class DashboardTile(sw.Layout):
    def __init__(
        self,
        gee_interface: GEEInterface,
        recipe: Recipe,
        theme_toggle=None,
        sepal_session=None,
    ):
        super().__init__()

        self._metadata = {"mount_id": "dashboard_tile"}
        self.theme_toggle = theme_toggle
        self.class_ = "d-block"
        self.summary_stats = None
        self.recipe = recipe
        self.gee_interface = gee_interface
        self.alert = Alert()
        self.sepal_session = sepal_session

        alert_dialog = AlertDialog(self.alert)

        self.dash_toolbar = DashToolbar(
            recipe.seplan,
            alert=self.alert,
            sepal_session=sepal_session,
            gee_interface=gee_interface,
        )

        # init the dashboard
        self.overall_dash = OverallDashboard(theme_toggle=self.theme_toggle)
        self.theme_dash = ThemeDashboard(theme_toggle=self.theme_toggle)
        self.children = [
            self.dash_toolbar,
            self.overall_dash,
            self.theme_dash,
            # Dialogs
            alert_dialog,
        ]

        self.dash_toolbar.compare_dialog.set_stats_content(
            overall_dashboard=self.overall_dash, theme_dashboard=self.theme_dash
        )

        self.recipe.dash_model.observe(self.reset, "reset_count")
        self.recipe.observe(self.reset, "recipe_session_path")

        self._configure_csv_export()
        self._configure_dashboard()

    def _configure_csv_export(self, *_) -> None:
        """Export the dashboard as a csv file."""

        def create_csv_task():
            def callback(*_):

                task = self.dash_toolbar.btn_download._task

                if task:
                    self.summary_stats = task.result

                    session_results_path = export_as_csv(self.summary_stats)

                    self.alert.add_msg(
                        f"File successfully saved in {session_results_path}", "success"
                    )

            return self.gee_interface.create_task(
                func=get_summary_statistics_async,
                key="create_csv_task",
                on_done=callback,
                on_error=lambda e: self.alert.add_msg(str(e), type_="error"),
            )

        self.dash_toolbar.btn_download.configure(
            task_factory=create_csv_task,
            start_args=(
                self.gee_interface,
                self.recipe,
            ),
        )

    def _configure_dashboard(self, *_):
        """Compute the restoration plan for the self.recipe and display the dashboard."""

        def create_dashboard_task():
            def callback(*_):

                task = self.dash_toolbar.btn_dashboard._task
                if task:
                    self.summary_stats = task.result

                    # set the content of the panels
                    self.overall_dash.set_summary([self.summary_stats])

                    # For the theme we need to extract the metadata from the seplan models
                    self.theme_dash.set_summary([self.recipe], [self.summary_stats])

            return self.gee_interface.create_task(
                func=get_summary_statistics_async,
                key="create_daskboard_task",
                on_done=callback,
                on_error=lambda e: self.alert.add_msg(str(e), type_="error"),
            )

        self.dash_toolbar.btn_dashboard.configure(
            task_factory=create_dashboard_task,
            start_args=(
                self.gee_interface,
                self.recipe,
            ),
        )

    def reset(self, *_):
        """Reset the dashboard to its initial state."""
        logger.debug("resetting the dashboard")
        self.summary_stats = None
        self.overall_dash.reset()
        self.theme_dash.reset()


class ThemeDashboard(sw.Card):
    seplan: Seplan
    "Seplan object used to retrieve the layer description and units"

    def __init__(self, theme_toggle=None):
        super().__init__()
        self.theme_toggle = theme_toggle
        self.title = sw.CardTitle(children=[cm.dashboard.theme.title])
        self.content = sw.CardText()
        self.alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        self.children = [self.title, self.alert, self.content]

    def get_summary_charts(
        self, recipes: Tuple[Recipe], summary_stats: Tuple[RecipeStatsDict]
    ) -> Tuple[BenefitChartsData, ConstraintChartsData, CostChartData]:
        """Get the summary charts for the benefit, cost and constraint themes

        ** Recipes are required here because we need to extract the metadata from the seplan models.
        """

        assert len(recipes) == len(
            summary_stats
        ), "The number of recipes and summary_stats should be the same"

        # We cannot put all the charts from the different scenarios in the same list because they
        # might have different layers

        # Set the default structure, based on the type
        benefit_charts: BenefitChartsData = {}  # type: ignore
        constraint_charts: ConstraintChartsData = {}  # type: ignore
        cost_charts: CostChartData = {"cost_layers": []}  # type: ignore

        for recipe, scenario_stats in zip(recipes, summary_stats):

            recipe_name, scenario_stats = list(scenario_stats.items())[0]

            for layer_id in recipe.seplan.benefit_model.ids:

                benefit_charts.setdefault(layer_id, [])

                aoi_names, values, colors, min_, max_ = parse_layer_data(
                    scenario_stats, layer_id
                )

                layer_data = recipe.seplan.benefit_model.get_layer_data(layer_id)

                w_chart = get_bars_chart(
                    categories=aoi_names,
                    values=[values],
                    custom_item_color=True,
                    custom_item_colors=[colors],
                    series_names=[layer_data.get("name")],
                    show_legend=False,
                    bars_width=50,
                    min_value=min_,
                    max_value=max_,
                    theme_toggle=self.theme_toggle,
                )

                # Get all the layers for the benefit theme
                benefit_charts[layer_id].append((recipe_name, layer_data, w_chart))

            # Get all the layers for the constraint theme
            for layer_id in recipe.seplan.constraint_model.ids:
                constraint_charts.setdefault(layer_id, [])

                layer_data = recipe.seplan.constraint_model.get_layer_data(layer_id)
                aoi_names, values, colors, *_ = parse_layer_data(
                    scenario_stats, layer_id
                )

                constraint_charts[layer_id].append(
                    (recipe_name, layer_data, values, colors)
                )

            # Each of the series has to be one of the costs in the cost model
            layers_data, aoi_names, values, colors, series_names = [], [], [], [], []
            for layer_id in recipe.seplan.cost_model.ids:

                layer_data = recipe.seplan.cost_model.get_layer_data(layer_id)

                layers_data.append(layer_data)
                aoi_name, value, *_ = parse_layer_data(scenario_stats, layer_id)
                aoi_names.append(aoi_name)
                values.append(value)
                series_names.append(layer_data["name"])
                # TODO: make the theme a traits
                colors.append(
                    PLOT_COLORS.get(layer_data["id"], {"dark": None}).get("dark")
                )

            w_chart = get_bars_chart(
                categories=aoi_names[0],
                values=values,
                series_names=series_names,
                series_colors=colors,
                bars_width=80,
                theme_toggle=self.theme_toggle,
            )
            cost_charts["cost_layers"].append((recipe_name, layers_data, w_chart))

        return benefit_charts, constraint_charts, cost_charts

    def get_benefit_panels(self, benefit_charts: BenefitChartsData):
        """Get the benefit panels for the dashboard"""

        ben = v.Html(tag="h2", children=[cm.theme.benefit.capitalize()])
        ben_txt = sw.Markdown("  \n".join(cm.dashboard.theme.benefit.description))
        ben_header = v.ExpansionPanelHeader(children=[ben])

        benefit_panels = []
        for layer_id, charts_data in benefit_charts.items():
            layer_data = charts_data[0][1]
            # Get all charts for that layer
            layer_charts = [chart for _, _, chart in charts_data]
            recipe_names = [recipe_name for recipe_name, _, _ in charts_data]
            layer_panel = LayerFull(layer_data, layer_charts, recipe_names)
            benefit_panels.append(layer_panel)

        ben_content = v.ExpansionPanelContent(children=[ben_txt, *benefit_panels])
        ben_panel = v.ExpansionPanel(children=[ben_header, ben_content])

        return ben_panel

    def get_cost_panels(self, cost_charts: CostChartData):
        """Get the cost panels for the dashboard"""

        layer_data = cost_charts["cost_layers"][0][1]
        recipe_names = [recipe_name for recipe_name, _, _ in cost_charts["cost_layers"]]

        cost = v.Html(tag="h2", children=[cm.theme.cost.capitalize()])
        cost_txt = sw.Markdown("  \n".join(cm.dashboard.theme.cost.description))
        cost_header = v.ExpansionPanelHeader(children=[cost])

        cost_panels = [
            LayerFull(
                layer_data,
                [chart for _, _, chart in cost_charts["cost_layers"]],
                recipe_names,
            )
        ]

        cost_content = v.ExpansionPanelContent(children=[cost_txt, *cost_panels])
        cost_panel = v.ExpansionPanel(children=[cost_header, cost_content])

        return cost_panel

    def get_constraint_panels(self, constraint_charts: ConstraintChartsData):
        """Get the constraint panels for the dashboard"""

        const = v.Html(tag="h2", children=[cm.theme.constraint.capitalize()])
        const_txt = sw.Markdown("  \n".join(cm.dashboard.theme.constraint.description))
        const_header = v.ExpansionPanelHeader(children=[const])

        constraint_charts_data = []
        for layer_id, constraint_charts in constraint_charts.items():
            layer_data = constraint_charts[0][1]
            values, colors = zip(
                *[(values, colors) for _, _, values, colors in constraint_charts]
            )

            constraint_charts_data.append(LayerPercentage(layer_data, values, colors))

        const_content = v.ExpansionPanelContent(
            children=[const_txt, *constraint_charts_data]
        )
        const_panel = v.ExpansionPanel(children=[const_header, const_content])

        return const_panel

    def set_summary(
        self, recipes: Tuple[Recipe], recipes_stats: Tuple[RecipeStatsDict]
    ):
        """Set the summary statistics for all the summary comming from different scenarios"""

        benefit_charts, constraint_charts, cost_charts = self.get_summary_charts(
            recipes, recipes_stats
        )

        ben_panel = self.get_benefit_panels(benefit_charts)
        cost_panel = self.get_cost_panels(cost_charts)
        const_panel = self.get_constraint_panels(constraint_charts)

        # create an expansion panel to store everything
        ep = v.ExpansionPanels(children=[ben_panel, cost_panel, const_panel])
        ep.value = 1

        self.content.children = [ep]

        # hide the alert
        self.alert.reset()

        return self

    def reset(self):
        """Reset the dashboard to its initial state."""
        self.__init__(theme_toggle=self.theme_toggle)


class OverallDashboard(sw.Card):
    def __init__(self, theme_toggle=None):
        self.theme_toggle = theme_toggle
        self.class_ = "my-2"
        super().__init__()
        self.title = sw.CardTitle(children=[cm.dashboard.region.title])
        self.content = sw.CardText()
        self.alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        self.children = [self.title, self.alert, self.content]

    def set_summary(self, recipes_stats: List[RecipeStatsDict]):
        """Set the summary statistics for all the summary comming from different scenarios"""

        logger.debug(
            f"OverallDashboard.set_summary, with theme_toggle: {self.theme_toggle}"
        )
        suitability_charts = get_suitability_charts(
            recipes_stats, theme_toggle=self.theme_toggle
        )

        # For the table, I need to display all of them in the same table
        suitability_table = get_summary_table(recipes_stats, "both")

        self.content.children = suitability_charts + [suitability_table]

        self.alert.reset()

    def reset(self):
        """Reset the dashboard to its initial state."""
        self.__init__(theme_toggle=self.theme_toggle)
