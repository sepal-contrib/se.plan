from typing import Dict, List

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw

from component import widget as cw
from component.message import cm
from component.model.recipe import Recipe
from component.scripts.statistics import parse_theme_stats
from component.widget.alert_state import AlertState

ID = "dashboard_widget"
"the dashboard tiles share id"


class DashboardTile(sw.Layout):
    def __init__(self):
        self._metadata = {"mount_id": "dashboard_tile"}
        self.class_ = "d-block"

        super().__init__()

    def build(self, recipe: Recipe, alert: AlertState):
        alert.set_state("new", "dashboard", "building")

        # init the dashboard
        self.overall_dash = OverallDashboard()
        self.theme_dash = ThemeDashboard()
        self.children = [
            self.overall_dash,
            self.theme_dash,
        ]

        alert.set_state("new", "dashboard", "done")


class ThemeDashboard(sw.Tile):
    def __init__(self):
        sw.Markdown(cm.dashboard.theme.txt)

        # TODO for no reason this alert is shared between DashThemeTile and
        # DashRegionTile. that's a wanted behaviour but I would like to have more control over it
        alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        # create the tile
        super().__init__(id_=ID, title=cm.dashboard.theme.title, alert=alert)

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
                    ben_layer.append(cw.LayerFull(name, values, names_colors))
                elif theme == "cost":
                    cost_layer.append(cw.LayerFull(name, values, names_colors))
                elif theme == "constraint":
                    const_layer.append(cw.LayerPercentage(name, values, names_colors))
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

        self.set_content([ep])

        # hide the alert
        self.alert.reset()

        return self


class OverallDashboard(sw.Tile):
    def __init__(self):
        super().__init__(id_=ID, title=cm.dashboard.region.title)

    def set_summary(self, summary_stats: List[Dict]):
        feats = []
        for aoi_data in summary_stats:
            aoi_name = next(iter(aoi_data))
            values = aoi_data[next(iter(aoi_data))]["suitability"]["values"]
            feats.append(cw.AreaSumUp(aoi_name, self.format_values(values)))

        self.set_content(feats)

        return self

    def format_values(self, raw):
        out_values = []
        for class_ in range(1, 7):
            index_i = next((i["sum"] for i in raw if i["image"] == class_), 0)
            out_values.append(index_i)

        return out_values
