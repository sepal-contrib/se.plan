import random

import pandas as pd
from sepal_ui import model
from traitlets import Any

from component import parameter as cp

layer_list = pd.read_csv(cp.layer_list).fillna('')

class CustomizeLayerModel(model.Model):
    
    layer_list = Any([
            {
                'name':     row.layer_name,
                'layer':    row.gee_asset,
                'unit':     row.unit,
                'weight' :  0,
                'theme' :   row.theme,
                'subtheme': row.subtheme,
                'operator' : row.operator,
            } for i, row in layer_list.iterrows()
        ]).tag(sync=True)
    
    def export_data(self):
        
        # remove eeimage parameter from every layer as it is not serializable 
        [layer.pop('eeimage', None) for layer in self.layer_list]
        
        return super().export_data()
        