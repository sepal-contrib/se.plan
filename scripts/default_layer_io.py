from .tile.custom_layer_tile import CustomizeLayerIo
from . import parameter as pm
import random


default_layer_io = CustomizeLayerIo()

for i, layer in enumerate(default_layer_io.layer_list):
    
    layer_df_line = pm.layer_list[pm.layer_list.layer_name == layer['name']].iloc[0]
    layer.update(
        layer  = layer_df_line.gee_asset if random.random() < 0.5 else f'user/custom/Layer{i}',
        weight = random.randint(0, 6) 
    )