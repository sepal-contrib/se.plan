class CustomizeLayerIo:
    
    def __init__(self):
        
        self.layer_list = [
            {
                'name'   : row.layer_name,
                'layer': row.gee_asset,
                'weight' : 0
            } for i, row in pm.layer_list.iterrows()
        ]
        
default_layer_io = CustomizeLayerIo()

for i, layer in enumerate(default_layer_io.layer_list):
    
    layer_df_line = pm.layer_list[pm.layer_list.layer_name == layer['name']].iloc[0]
    layer.update(
        layer  = layer_df_line.gee_asset if random.random() < 0.5 else f'user/custom/Layer{i}',
        weight = random.randint(0, 6) 
    )