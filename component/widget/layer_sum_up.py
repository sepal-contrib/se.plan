import ipyvuetify as v 
import pandas as pd

from component import parameter as cp

class LayerFull(v.Layout):
    
    COLORS = cp.gradient(5) + ['grey']
    
    def __init__(self, layer_name, values=[0,0,0,0,0,0], total=100):
        
        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna('')
        layer_row = layer_list[layer_list.layer_name == layer_name]
        
        if len(layer_row) != 1:
            raise IndexError(f"The layer {layer_name} is not part of the existing layers of the application. Please contact our maintainer.")
        
        # build the internal details        
        details = v.ExpansionPanels(xs12=True, class_="mt-3", children= [
            v.ExpansionPanel(children = [
                v.ExpansionPanelHeader(children=['Details'], expand_icon='mdi-help-circle-outline', disable_icon_rotate=True),
                v.ExpansionPanelContent(children=[layer_row.layer_info.values[0]])
            ])
        ])
        
        # create a title with the layer name
        title = v.Html(class_="mt-2 mb-2", xs12= True, tag="h3", children=[layer_name])
        
        # create the result table
        head = [v.Html(tag='thead', children=[v.Html(tag='tr', children=[
            v.Html(tag='th', children = [f"value ({layer_row.unit.values[0]})"]),
            v.Html(tag='th', children = ["ratio"])
        ])])]
        
        rows = []
        for i, val in enumerate(values):
            
            if val != 0:
                row = v.Html(tag='tr', children=[
                    v.Html(tag='td', children=[f"{val}"]),
                    v.Html(tag='td', children=[v.ProgressLinear(
                        v_model=int(val/total*100), 
                        color=self.COLORS[i], 
                        background_opacity=0.1, 
                        height=10, 
                        rounded=True, 
                        background_color='grey', 
                        dense=True
                    )])
                ])
            
                rows.append(row)

        body = [v.Html(tag='tbody', children = rows)]
        table = v.SimpleTable(xs12=True, children = head + body)
        
        super().__init__(
            class_ = "ma-5",
            row=True,
            children=[
                v.Flex(xs12=True, children = [title]),
                v.Flex(xs12=True, children=[table]),
                v.Flex(xs12=True, children=[details])
            ]
        )
        
#class layerPercentage()