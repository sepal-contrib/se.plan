from pathlib import Path
from typing import Dict, List

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import widget as cw
from component.message import cm
from component.model.recipe import Recipe
from component.scripts.logger import logger
from component.scripts.compute import export_as_csv
from component.scripts.plots import (
    get_bars_chart,
    get_individual_charts,
    get_stacked_bars_chart,
    parse_layer_data,
)
from component.scripts.seplan import Seplan
from component.scripts.statistics import get_summary_statistics
from component.types import SummaryStatsDict
from component.widget.alert_state import Alert, AlertDialog
from component.widget.area_sum_up import get_summary_table
from component.widget.custom_widgets import DashToolBar


class DashboardTile(sw.Layout):
    def __init__(self, recipe: Recipe):
        super().__init__()

        self._metadata = {"mount_id": "dashboard_tile"}
        self.class_ = "d-block"
        self.summary_stats = None

        self.recipe = recipe

        dash_toolbar = DashToolBar(recipe.seplan)

        self.alert = Alert()
        # wrap the alert in a dialog
        alert_dialog = AlertDialog(self.alert)

        # init the dashboard
        self.overall_dash = OverallDashboard()
        self.theme_dash = ThemeDashboard(recipe.seplan)
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

        dash_toolbar.btn_dashboard.on_event("click", self._dashboard)
        dash_toolbar.btn_download.on_event("click", self.csv_export)

        self.recipe.dash_model.observe(self.reset, "reset_count")

    def csv_export(self, *_):
        """Export the dashboard as a csv file."""
        self.summary_stats = get_summary_statistics(self.recipe.seplan)
        recipe_session_name = Path(self.recipe.recipe_session_path).name

        # save the dashboard as a csv
        session_results_path = export_as_csv(recipe_session_name, self.summary_stats)

        self.alert.add_msg(
            f"File successfully saved in {session_results_path}", "success"
        )

    def _dashboard(self, *_):
        """Compute the restoration plan and display the map."""

        if not self.summary_stats:
            logger.info("No dashboard to display")
            self.summary_stats = get_summary_statistics(self.recipe.seplan)

        # set the content of the panels
        self.overall_dash.set_summary(self.summary_stats)
        self.theme_dash.set_summary(self.summary_stats)

    def reset(self, *_):
        """Reset the dashboard to its initial state."""
        logger.info("resettig the dashboard")
        self.summary_stats = None
        self.overall_dash.reset()
        self.theme_dash.reset()


class ThemeDashboard(sw.Card):
    seplan: Seplan
    "Seplan object used to retrieve the layer description and units"

    def __init__(self, seplan: Seplan):
        super().__init__()
        self.seplan = seplan
        self.title = sw.CardTitle(children=[cm.dashboard.theme.title])
        self.content = sw.CardText()
        self.alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        self.children = [self.title, self.alert, self.content]

    def set_summary(self, summary_stats: SummaryStatsDict):
        # We need to get the labels from the seplan models

        benefit_charts, cost_charts, constraint_charts = [], [], []

        for layer_id in self.seplan.benefit_model.ids:

            aoi_names, values, colors = parse_layer_data(summary_stats, layer_id)

            layer_data = self.seplan.benefit_model.get_layer_data(layer_id)
            w_chart = get_bars_chart(
                aoi_names,
                [values],
                [colors],
                [layer_data["name"]],
                custom_color=True,
                show_legend=False,
            )

            # Get all the layers for the benefit theme
            benefit_charts.append(cw.LayerFull(layer_data, w_chart))

        # Each of the series has to be one of the costs in the cost model
        aoi_names, values, colors, series_names = [], [], [], []
        for layer_id in self.seplan.cost_model.ids:

            layer_data = self.seplan.cost_model.get_layer_data(layer_id)

            aoi_name, value, color = parse_layer_data(summary_stats, layer_id)
            aoi_names.append(aoi_name)
            values.append(value)
            colors.append(color)
            series_names.append(layer_data["name"])

        w_chart = get_bars_chart(
            aoi_names[0], values, colors, series_names, bars_width=70
        )
        cost_charts = [cw.LayerFull(layer_data, w_chart)]

        # Get all the layers for the constraint theme
        for layer_id in self.seplan.constraint_model.ids:

            layer_data = self.seplan.constraint_model.get_layer_data(layer_id)
            aoi_names, values, colors = parse_layer_data(summary_stats, layer_id)

            constraint_charts.append(cw.LayerPercentage(layer_data, values, colors))

        ben = v.Html(tag="h2", children=[cm.theme.benefit.capitalize()])
        ben_txt = sw.Markdown("  \n".join(cm.dashboard.theme.benefit.description))
        ben_header = v.ExpansionPanelHeader(children=[ben])
        ben_content = v.ExpansionPanelContent(children=[ben_txt, *benefit_charts])
        ben_panel = v.ExpansionPanel(children=[ben_header, ben_content])

        cost = v.Html(tag="h2", children=[cm.theme.cost.capitalize()])
        cost_txt = sw.Markdown("  \n".join(cm.dashboard.theme.cost.description))
        cost_header = v.ExpansionPanelHeader(children=[cost])
        cost_content = v.ExpansionPanelContent(children=[cost_txt, *cost_charts])
        cost_panel = v.ExpansionPanel(children=[cost_header, cost_content])

        const = v.Html(tag="h2", children=[cm.theme.constraint.capitalize()])
        const_txt = sw.Markdown("  \n".join(cm.dashboard.theme.constraint.description))
        const_header = v.ExpansionPanelHeader(children=[const])
        const_content = v.ExpansionPanelContent(
            children=[const_txt, *constraint_charts]
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
        self.__init__(self.seplan)


class OverallDashboard(sw.Card):
    def __init__(self):
        self.class_ = "my-2"
        super().__init__()
        self.title = sw.CardTitle(children=[cm.dashboard.region.title])
        self.content = sw.CardText()
        self.alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        self.children = [self.title, self.alert, self.content]

    def set_summary(self, summary_stats: List[Dict]):

        suitability_charts = get_stacked_bars_chart(summary_stats)
        suitability_table = get_summary_table(summary_stats, "both")
        charts = get_individual_charts(summary_stats)

        self.content.children = [suitability_charts] + [suitability_table]

        self.alert.reset()

    def reset(self):
        """Reset the dashboard to its initial state."""
        self.__init__()
