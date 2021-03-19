import ipyvuetify as v 
from sepal_ui import sepalwidgets as sw
import pandas as pd
import numpy as np

from component import parameter as cp



class layerRecipe(v.Layout, sw.SepalWidget):
    
    # load the layers 
    LAYER_LIST = pd.read_csv(cp.layer_list).fillna('')
    LAYER_LIST = LAYER_LIST.rename(columns={"gee_asset": "layer", "layer_name": "name"})
    LAYER_LIST["weight"] = [0 for i in range(len(LAYER_LIST))]
    
    
    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)
        self.row = True
        self.class_ = "ma-5"
        
        # display the default values (all with default layer and 0 valued weight)
        self.digest_layers()
        
    def digest_layers(self, layer_list=None):
        """
        Digest the layers as a json list. This list should be composed of at least 5 information : name, layer, weight, theme and subtheme
        When digestiong, the layout will represent each layer sorted by categories
        fore each one of them if the layer used is the default one we'll write default, if not the name of the layer. 
        for each one of them the value of the weight will also be set
        """
        
        # read the json str into a panda dataframe
        layer_list = pd.DataFrame(layer_list) if layer_list else self.LAYER_LIST
        
        # get all the themes 
        themes = np.unique(layer_list.theme)
        
        themes_layout = []
        for theme in themes:
            
            # filter the layers 
            tmp_layers = layer_list[layer_list.theme == theme]
            
            # add the theme title 
            themes_layout.append(v.Html(xs12 = True, class_ = 'mt-6', tag="h2", children=[theme.capitalize()]))
            
            # loop in these layers and create the widgets
            theme_layer_widgets = []
            for i, row in tmp_layers.iterrows():
                
                # get the original layer asset 
                original_asset = self.LAYER_LIST[self.LAYER_LIST.name == row['name']]['layer'].values[0]

                # cannot make the slots work with icons so I need to move to intermediate layout 
                # the color have 7 values and there are only 5 weight 
                theme_layer_widgets.append(v.Row(
                    class_ = 'ml-2 mr-2',
                    children = [
                        v.TextField(
                            hint = row["layer"] if row["layer"] != original_asset else "default",
                            persistent_hint = True,
                            color = cp.gradient(11)[row['weight']],
                            readonly = True,
                            v_model = row['name']
                        ),
                        v.Icon(
                            class_ = 'ml-2',
                            color = cp.gradient(11)[row['weight']],
                            children = [f"mdi-numeric-{row['weight']}-circle"]
                        )
                    ]
                ))
                
            # add the lines to the layout
            themes_layout.append(v.Layout(row = True, children=theme_layer_widgets))
            
        # add the layout element to the global layout 
        self.children = themes_layout
        
        return self
                
        
        
        
        
        
        
        
        
        
        