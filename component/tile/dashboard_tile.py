from random import random

from sepal_ui import sepalwidgets as sw
import pandas as pd
import ipyvuetify as v

from component.message import cm
from component import widget as cw
from component import parameter as cp

class DashThemeTile(sw.Tile):
    
    def __init__(self):
        
        txt = sw.Markdown(cm.dashboard.theme.txt)
        
        # create the tile 
        super().__init__(
            id_ = "dashboard_widget",
            title = cm.dashboard.theme.title,
        )


    def dev_set_summary(self, json_themes_values, aoi_name, colors):
        benefits_layer = []
        constraints_layer = []
        costs_layer = []

        for k,val in json_themes_values.items():
            for layer in json_themes_values[k]:
                if k == 'name':
                    # have name column as it will be good to add this while displaying at some point
                    continue
                name = layer
                try:
                    values = json_themes_values[k][layer]['values']
                    if k == 'benefits':
                        benefits_layer.append(cw.LayerFull(name, values, aoi_name, colors))
                    elif k == 'costs':
                        costs_layer.append(cw.LayerFull(name, values, aoi_name, colors))
                    elif k == 'constraints':
                        constraints_layer.append(cw.LayerPercentage(name, values, colors))

                except Exception as e:
                    print(name, 'not found',e)
                    continue
        
        benefits = v.Html(tag='h2', children= ['Benefits'])
        benefits_txt = sw.Markdown('  /n'.join(cm.dashboard.theme.benefit))
        
        costs = v.Html(tag='h2', children= ['Costs'])
        costs_txt = sw.Markdown('  /n'.join(cm.dashboard.theme.cost))
        
        constraints = v.Html(tag='h2', children=['Constraints'])
        constraints_txt = sw.Markdown('  /n'.join(cm.dashboard.theme.constraint))
        
        # create an expansion panel to store everything 
        ep = v.ExpansionPanels(
            children = [
                v.ExpansionPanel(
                    children = [
                        v.ExpansionPanelHeader(children = [benefits]),
                        v.ExpansionPanelContent(children=[benefits_txt] + benefits_layer)
                    ]
                ),
                v.ExpansionPanel(
                    children = [
                        v.ExpansionPanelHeader(children = [costs]),
                        v.ExpansionPanelContent(children= [costs_txt] + costs_layer)
                    ]
                ),
                v.ExpansionPanel(
                    children = [
                        v.ExpansionPanelHeader(children = [constraints]),
                        v.ExpansionPanelContent(children=[constraints_txt] + constraints_layer)
                    ]
                )
            ]
        )
        
        self.set_content([ep])
        
        return self
            
class DashRegionTile(sw.Tile):
    
    def __init__(self):
        
        super().__init__(
            id_ = 'dashboard_widget',
            title = cm.dashboard.region.title
        )
        
    def set_summary(self, json_feature_values):
    
        feats = []
        for feat in json_feature_values:
            raw = json_feature_values[feat]['values']
            feats.append(cw.AreaSumUp(feat, self.format_values(raw)))
                         
        self.set_content(feats)
                         
        return self
                         
    def format_values(self, raw):
        computed = [i['image'] for i in raw]
        out_values = []
        for i in range(1,7):
            if i in computed:
                index_i = next(item['sum'] for item in raw if item['image'] == i)
            else:
                index_i = 0
            out_values.append(index_i)

        return out_values