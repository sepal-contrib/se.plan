from pathlib import Path
from typing import Dict, List

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import widget as cw
from component.message import cm
from component.model.recipe import Recipe
from component.scripts.compute import export_as_csv
from component.scripts.seplan import Seplan
from component.scripts.statistics import get_summary_statistics, parse_theme_stats
from component.widget.alert_state import Alert, AlertDialog, AlertState
from component.widget.custom_widgets import DashToolBar

ID = "dashboard_widget"
"the dashboard tiles share id"


class DashboardTile(sw.Layout):
    def __init__(self):
        super().__init__()

        self._metadata = {"mount_id": "dashboard_tile"}
        self.class_ = "d-block"
        self.summary_stats = None

    def build(self, recipe: Recipe, build_alert: AlertState):
        """Build the dashboard tile."""
        build_alert.set_state("new", "dashboard", "building")
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

        build_alert.set_state("new", "dashboard", "done")

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
        self.summary_stats = get_summary_statistics(self.recipe.seplan)

        # set the content of the panels
        self.overall_dash.set_summary(self.summary_stats)
        self.theme_dash.set_summary(self.summary_stats)

    def reset(self):
        """Reset the dashboard to its initial state."""
        print("resettig the dashboard")
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

    def set_summary(self, summary_stats):
        # Extract the aoii names and color from summary_stats
        names_colors = []
        for aoi_data in summary_stats:
            aoi_name = next(iter(aoi_data))
            color = aoi_data[aoi_name]["color"]
            names_colors.append((aoi_name, color))

        themes_values = parse_theme_stats(summary_stats)

        # init the layer list
        ben_layer, const_layer, cost_layer = [], [], []

        # reorder the aois with the main one in first
        # TODO: check this reorder
        names_colors = names_colors[::-1]

        # filter the names of the aois  from the json_theme values

        for theme, layers in themes_values.items():
            for name, values in layers.items():
                values = values["values"]
                if theme == "benefit":
                    ben_layer.append(
                        cw.LayerFull(
                            name, values, names_colors, self.seplan.benefit_model
                        )
                    )
                elif theme == "cost":
                    cost_layer.append(
                        cw.LayerFull(name, values, names_colors, self.seplan.cost_model)
                    )
                elif theme == "constraint":
                    const_layer.append(
                        cw.LayerPercentage(
                            name, values, names_colors, self.seplan.constraint_model
                        )
                    )
                else:
                    continue  # Aois names are also stored in the dictionary

        ben = v.Html(tag="h2", children=[cm.theme.benefit.capitalize()])
        ben_txt = sw.Markdown("  \n".join(cm.dashboard.theme.benefit.description))
        ben_header = v.ExpansionPanelHeader(children=[ben])
        ben_content = v.ExpansionPanelContent(children=[ben_txt, *ben_layer])
        ben_panel = v.ExpansionPanel(children=[ben_header, ben_content])

        cost = v.Html(tag="h2", children=[cm.theme.cost.capitalize()])
        cost_txt = sw.Markdown("  \n".join(cm.dashboard.theme.cost.description))
        cost_header = v.ExpansionPanelHeader(children=[cost])
        cost_content = v.ExpansionPanelContent(children=[cost_txt, *cost_layer])
        cost_panel = v.ExpansionPanel(children=[cost_header, cost_content])

        const = v.Html(tag="h2", children=[cm.theme.constraint.capitalize()])
        const_txt = sw.Markdown("  \n".join(cm.dashboard.theme.constraint.description))
        const_header = v.ExpansionPanelHeader(children=[const])
        const_content = v.ExpansionPanelContent(children=[const_txt, *const_layer])
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
        super().__init__()
        self.title = sw.CardTitle(children=[cm.dashboard.region.title])
        self.content = sw.CardText()
        self.alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        self.children = [self.title, self.alert, self.content]

    def set_summary(self, summary_stats: List[Dict]):
        feats = []
        for aoi_data in summary_stats:
            aoi_name = next(iter(aoi_data))
            values = aoi_data[next(iter(aoi_data))]["suitability"]["values"]
            feats.append(cw.AreaSumUp(aoi_name, self.format_values(values)))

        self.content.children = feats

        # hide the alert
        self.alert.reset()

        return self

    def format_values(self, raw):
        out_values = []
        for class_ in range(1, 7):
            index_i = next((i["sum"] for i in raw if i["image"] == class_), 0)
            out_values.append(index_i)

        return out_values

    def reset(self):
        """Reset the dashboard to its initial state."""
        self.__init__()
