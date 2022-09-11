from random import random

from sepal_ui import sepalwidgets as sw
import pandas as pd
import ipyvuetify as v

from component.message import cm
from component import widget as cw
from component import parameter as cp
from component import scripts as cs

import logging
ID = "dashboard_widget"
"the dashboard tiles share id"


class DashThemeTile(sw.Tile):
    def __init__(self):

        txt = sw.Markdown(cm.dashboard.theme.txt)

        # TODO for no reason this alert is shared between DashThemeTile and
        # DashRegionTile. that's a wanted behaviour but I would like to have more control over it
        alert = sw.Alert().add_msg(cm.dashboard.theme.disclaimer, "warning")

        # create the tile
        super().__init__(id_=ID, title=cm.dashboard.theme.title, alert=alert)

    def dev_set_summary(self, json_themes_values, aoi_names, colors):

        # init the layer list
        ben_layer, const_layer, cost_layer = [], [], []

        # reorder the aois with the main one in first
        aoi_names = aoi_names[::-1]

        # filter the names of the aois  from the json_theme values
        json_themes_values.pop("names", None)

        for theme, layers in json_themes_values.items():
            for name, values in layers.items():

                values = values["values"]
                if theme == "benefit":
                    ben_layer.append(cw.LayerFull(name, values, aoi_names, colors))
                elif theme == "cost":
                    cost_layer.append(cw.LayerFull(name, values, aoi_names, colors))
                elif theme == "constraint":
                    const_layer.append(cw.LayerPercentage(name, values, colors))
                else:
                    continue  # Aois names are also stored in the dictionary

        ben = v.Html(tag="h2", children=[cm.theme.benefit.capitalize()])
        ben_txt = sw.Markdown("  \n".join(cm.dashboard.theme.benefit.description))
        ben_header = v.ExpansionPanelHeader(children=[ben])
        ben_content = v.ExpansionPanelContent(children=[ben_txt] + ben_layer)
        ben_panel = v.ExpansionPanel(children=[ben_header, ben_content])

        cost = v.Html(tag="h2", children=[cm.theme.cost.capitalize()])
        cost_txt = sw.Markdown("  \n".join(cm.dashboard.theme.cost.description))
        cost_header = v.ExpansionPanelHeader(children=[cost])
        cost_content = v.ExpansionPanelContent(children=[cost_txt] + cost_layer)
        cost_panel = v.ExpansionPanel(children=[cost_header, cost_content])

        const = v.Html(tag="h2", children=[cm.theme.constraint.capitalize()])
        const_txt = sw.Markdown("  \n".join(cm.dashboard.theme.constraint.description))
        const_header = v.ExpansionPanelHeader(children=[const])
        const_content = v.ExpansionPanelContent(children=[const_txt] + const_layer)
        const_panel = v.ExpansionPanel(children=[const_header, const_content])

        # create an expansion panel to store everything
        ep = v.ExpansionPanels(children=[ben_panel, cost_panel, const_panel])
        ep.value = 1

        self.set_content([ep])

        # hide the alert
        self.alert.reset()

        return self


class DashRegionTile(sw.Tile):
    def __init__(self):

        super().__init__(id_=ID, title=cm.dashboard.region.title)

    def set_summary(self, json_feature_values):

        feats = []
        for feat in json_feature_values:
            raw = json_feature_values[feat]["values"]
            feats.append(cw.AreaSumUp(feat, self.format_values(raw)))

        self.set_content(feats)

        return self

    def format_values(self, raw):
        out_values = []
        for class_ in range(1, 7):
            index_i = next((i["sum"] for i in raw if i["image"] == class_), 0)
            out_values.append(index_i)

        return out_values

    
class DashCarbonTile(sw.Tile):
    def __init__(self):
        super().__init__(id_=ID, title='Summary of forest carbon regrowth potential' )#todo: update entry at:cm.dashboard.{carbon}.title
        self.carbon = cp.chapman_richards_growth_params
        self.criterias = [self.carbon[k]['name'] for k, v in self.carbon.items()]



    def set_summary(self, json_feature_values):
        self.json_feature_values = json_feature_values
        self.select = sw.Select(
            disabled=False,  # disabled until the aoi is selected
            class_="mt-5",
            small_chips=True,
            v_model=[],
            items=self.criterias,
            label='Forest growth climate',
            multiple=False,
            deletable_chips=False,
            persistent_hint=True,
            # hint=cm.constraints.error.no_aoi,
        )
        self.set_content([self.select])
        
        self.select.observe(self._on_change, "v_model")

            
        return self
        
    def _on_change(self, change):
        """remove the menu-props if at least 1 items is added"""
# {'SLV': {'total': 2048660.1375282384, 'values': [{'image': 1.0, 'sum': 311744.6777816738}, {'image': 2.0, 'sum': 618409.5477976433}, {'image': 3.0, 'sum': 476404.1678195145}, {'image': 4.0, 'sum': 170626.89727065992}, {'image': 5.0, 'sum': 73769.73928468348}, {'image': 6.0, 'sum': 397705.10757406347}]}}
        #todo this needs to be changed to something better
        carbon_id = "_".join(self.select.v_model.lower().split(" "))
        carbon_key = self.carbon[carbon_id]
        # carbon_params = cs.get_growth_params(self.carbon, carbon_key)
        feats = []
        for feat in self.json_feature_values:
            raw = self.json_feature_values[feat]["values"]
            feats.append(cw.CarbonSumUp(feat, carbon_key, self.format_values(raw)))
            
        self.set_content(feats)
        
        return self
    
    def format_values(self, raw):
        out_values = []
        for class_ in range(1, 7):
            index_i = next((i["sum"] for i in raw if i["image"] == class_), 0)
            out_values.append(index_i)

        return out_values