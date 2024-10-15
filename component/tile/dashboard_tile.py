from typing import List, Tuple
from component.types import (
    BenefitChartsData,
    ConstraintChartsData,
    CostChartData,
    RecipeStatsDict,
)

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import widget as cw
from component.message import cm
from component.model.recipe import Recipe
from component.parameter.vis_params import PLOT_COLORS
from component.scripts.logger import logger
from component.scripts.compute import export_as_csv
from component.scripts.plots import (
    get_bars_chart,
    get_suitability_charts,
    parse_layer_data,
)
from component.scripts.seplan import Seplan
from component.scripts.statistics import get_summary_statistics
from component.widget.alert_state import Alert, AlertDialog
from component.widget.suitability_table import get_summary_table
from component.widget.custom_widgets import DashToolbar
from component.widget.dashboard_layer_panels import LayerFull, LayerPercentage


class DashboardTile(sw.Layout):
    def __init__(self, recipe: Recipe):
        super().__init__()

        self._metadata = {"mount_id": "dashboard_tile"}
        self.class_ = "d-block"
        self.summary_stats = None

        self.recipe = recipe

        dash_toolbar = DashToolbar(recipe.seplan)

        self.alert = Alert()
        # wrap the alert in a dialog
        alert_dialog = AlertDialog(self.alert)

        # init the dashboard
        self.overall_dash = OverallDashboard()
        self.theme_dash = ThemeDashboard()
        self.children = [
            dash_toolbar,
            self.overall_dash,
            self.theme_dash,
            # Dialogs
            alert_dialog,
        ]

        self._dashboard = su.loading_button(self.alert, dash_toolbar.btn_dashboard)(
            self._dashboard
        )
        self.csv_export = su.loading_button(self.alert, dash_toolbar.btn_download)(
            self.csv_export
        )

        dash_toolbar.compare_dialog.set_stats_content(
            overal_dashboard=self.overall_dash, theme_dashboard=self.theme_dash
        )

        dash_toolbar.btn_dashboard.on_event("click", self._dashboard)
        dash_toolbar.btn_download.on_event("click", self.csv_export)

        self.recipe.dash_model.observe(self.reset, "reset_count")

    def csv_export(self, *_) -> None:
        """Export the dashboard as a csv file."""
        self.summary_stats = get_summary_statistics(self.recipe)

        # save the dashboard as a csv
        session_results_path = export_as_csv(self.summary_stats)

        self.alert.add_msg(
            f"File successfully saved in {session_results_path}", "success"
        )

    def _dashboard(self, *_):
        """Compute the restoration plan for the self.recipe and display the dashboard."""

        if not self.summary_stats:
            logger.info("No dashboard to display")
            self.summary_stats = get_summary_statistics(self.recipe)

        # set the content of the panels
        self.overall_dash.set_summary([self.summary_stats])

        # For the theme we need to extract the metadata from the seplan models
        self.theme_dash.set_summary([self.recipe], [self.summary_stats])

    def reset(self, *_):
        """Reset the dashboard to its initial state."""
        logger.info("resettig the dashboard")
        self.summary_stats = None
        self.overall_dash.reset()
        self.theme_dash.reset()


class ThemeDashboard(sw.Card):
    seplan: Seplan
    "Seplan object used to retrieve the layer description and units"

    def __init__(self):
        super().__init__()
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

                aoi_names, values, colors = parse_layer_data(scenario_stats, layer_id)
                layer_data = recipe.seplan.benefit_model.get_layer_data(layer_id)

                w_chart = get_bars_chart(
                    categories=aoi_names,
                    values=[values],
                    custom_item_color=True,
                    custom_item_colors=[colors],
                    series_names=[layer_data.get("name")],
                    show_legend=False,
                    bars_width=50,
                )

                # Get all the layers for the benefit theme
                benefit_charts[layer_id].append((recipe_name, layer_data, w_chart))

            # Get all the layers for the constraint theme
            for layer_id in recipe.seplan.constraint_model.ids:
                constraint_charts.setdefault(layer_id, [])

                layer_data = recipe.seplan.constraint_model.get_layer_data(layer_id)
                aoi_names, values, colors = parse_layer_data(scenario_stats, layer_id)

                constraint_charts[layer_id].append(
                    (recipe_name, layer_data, values, colors)
                )

            # Each of the series has to be one of the costs in the cost model
            aoi_names, values, colors, series_names = [], [], [], []
            for layer_id in recipe.seplan.cost_model.ids:

                layer_data = recipe.seplan.cost_model.get_layer_data(layer_id)

                aoi_name, value, _ = parse_layer_data(scenario_stats, layer_id)
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
            )
            cost_charts["cost_layers"].append((recipe_name, layer_data, w_chart))

        return benefit_charts, constraint_charts, cost_charts

    def set_summary(
        self, recipes: Tuple[Recipe], recipes_stats: Tuple[RecipeStatsDict]
    ):
        """Set the summary statistics for all the summary comming from different scenarios"""

        benefit_charts, constraint_charts, cost_charts = self.get_summary_charts(
            recipes, recipes_stats
        )

        ben = v.Html(tag="h2", children=[cm.theme.benefit.capitalize()])
        ben_txt = sw.Markdown("  \n".join(cm.dashboard.theme.benefit.description))
        ben_header = v.ExpansionPanelHeader(children=[ben])

        benefit_panels = []
        for layer_id, charts_data in benefit_charts.items():
            layer_data = recipes[0].seplan.benefit_model.get_layer_data(layer_id)
            # Get all charts for that layer
            layer_charts = [chart for _, _, chart in charts_data]
            layer_panel = LayerFull(layer_data, layer_charts)
            benefit_panels.append(layer_panel)

        ben_content = v.ExpansionPanelContent(children=[ben_txt, *benefit_panels])
        ben_panel = v.ExpansionPanel(children=[ben_header, ben_content])

        cost = v.Html(tag="h2", children=[cm.theme.cost.capitalize()])
        cost_txt = sw.Markdown("  \n".join(cm.dashboard.theme.cost.description))
        cost_header = v.ExpansionPanelHeader(children=[cost])

        cost_panels = [
            LayerFull(layer_data, [chart for _, _, chart in cost_charts["cost_layers"]])
        ]

        cost_content = v.ExpansionPanelContent(children=[cost_txt, *cost_panels])
        cost_panel = v.ExpansionPanel(children=[cost_header, cost_content])

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

        # create an expansion panel to store everything
        ep = v.ExpansionPanels(children=[ben_panel, cost_panel, const_panel])
        ep.value = 1

        self.content.children = [ep]

        # hide the alert
        self.alert.reset()

        return self

    def reset(self):
        """Reset the dashboard to its initial state."""
        self.__init__()


class OverallDashboard(sw.Card):
    def __init__(self):
        self.class_ = "my-2"
        super().__init__()
        self.title = sw.CardTitle(children=[cm.dashboard.region.title])
        self.content = sw.CardText()
        self.alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        self.children = [self.title, self.alert, self.content]

    def set_summary(self, recipes_stats: List[RecipeStatsDict]):
        """Set the summary statistics for all the summary comming from different scenarios"""

        suitability_charts = get_suitability_charts(recipes_stats)

        # For the table, I need to display all of them in the same table
        suitability_table = get_summary_table(recipes_stats, "both")

        self.content.children = suitability_charts + [suitability_table]

        self.alert.reset()

    def reset(self):
        """Reset the dashboard to its initial state."""
        self.__init__()
