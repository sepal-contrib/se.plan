import random

import pandas as pd

from component import parameter as cp

layer_list = pd.read_csv(cp.layer_list).fillna('')

class CustomizeLayerIo:
    
    def __init__(self):
        
        self.layer_list = [
            {
                'name':     row.layer_name,
                'layer':    row.gee_asset,
                'unit':     row.unit,
                'weight' :  0,
                'theme' :   row.theme,
                'subtheme': row.subtheme
            } for i, row in layer_list.iterrows()
        ]
        
default_layer_io = CustomizeLayerIo()

for i, layer in enumerate(default_layer_io.layer_list):
    
    layer_df_line = layer_list[layer_list.layer_name == layer['name']].iloc[0]
    layer.update(
        layer  = layer_df_line.gee_asset.strip(),
        weight = random.randint(0, 5) 
    )
    if layer['theme'] != 'benefits':
        layer.update(weight=random.randint(0,1))