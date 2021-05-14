import json

import ipyvuetify as v 
from sepal_ui import sepalwidgets as sw
import pandas as pd
import numpy as np

from component import parameter as cp



class layerRecipe(v.ExpansionPanels, sw.SepalWidget):
    
    # load the layers 
    LAYER_LIST = pd.read_csv(cp.layer_list).fillna('')
    LAYER_LIST = LAYER_LIST.rename(columns={"gee_asset": "layer", "layer_name": "name"})
    LAYER_LIST["weight"] = [0 for i in range(len(LAYER_LIST))]
    
    
    def __init__(self):
        
        super().__init__(class_='mt-5 mb-5', accordion=True, focusable=True)
        
        # display the default values (all with default layer and 0 valued weight)
        self.digest_layers()
        
    def digest_layers(self, layer_io=None, question_io=None):
        """
        Digest the layers as a json list. This list should be composed of at least 5 information : name, layer, theme and subtheme
        When digestion, the layout will represent each layer sorted by categories
        fore each one of them if the layer used is the default one we'll write default, if not the name of the layer. 
        for each one of them the value of the weight will also be set
        """
        
        if layer_io == None or question_io == None:
            return self
        
        # read the json str into a panda dataframe
        layer_list = layer_io.layer_list
        layer_list = pd.DataFrame(layer_list) if layer_list else self.LAYER_LIST
        
        # get all the themes 
        themes = np.unique(layer_list.theme)
        
        ep_content = []
        for theme in themes:
            
            # filter the layers 
            tmp_layers = layer_list[layer_list.theme == theme]
            
            # add the theme title 
            title = v.ExpansionPanelHeader(children=[theme.capitalize()])
            
            # loop in these layers and create the widgets
            theme_layer_widgets = []
            for i, row in tmp_layers.iterrows():
                
                # get the original layer asset 
                original_asset = self.LAYER_LIST[self.LAYER_LIST.name == row['name']]['layer'].values[0]

                # cannot make the slots work with icons so I need to move to intermediate layout 
                # the color have 7 values and there are only 5 weight 
                if row['theme'] == 'benefits':
                    
                    # get the weight from questionnaire
                    weight = json.loads(question_io.priorities)[row['subtheme']]
                    
                    # create the widget
                    theme_layer_widgets.append(v.Row(
                        class_ = 'ml-2 mr-2',
                        children = [
                            v.TextField(
                                small=True,
                                hint = row["layer"] if row["layer"] != original_asset else "default",
                                persistent_hint = True,
                                color = cp.gradient(5)[weight],
                                readonly = True,
                                v_model = row['name']
                            ),
                            v.Icon(
                                class_ = 'ml-2',
                                color = cp.gradient(5)[weight],
                                children = [f"mdi-numeric-{weight}-circle"]
                            )
                        ]
                    ))
                elif row['name'] not in ["Terrestrial ecoregions", 'Current land cover', 'Establishment cost', 'Current forest or ubran landscape', 'Current tree cover less than potential']:
                    
                    # get the activation from questionnaire_io 
                    active = json.loads(question_io.constraints)[row['name']] != -1
                    
                    theme_layer_widgets.append(v.Row(
                        class_ = 'ml-2 mr-2',
                        children = [
                            v.TextField(
                                small=True,
                                hint = row["layer"] if row["layer"] != original_asset else "default",
                                persistent_hint = True,
                                color = cp.gradient(2)[active],
                                readonly = True,
                                v_model = row['name']
                            ),
                            v.Icon(
                                class_ = 'ml-2',
                                color = cp.gradient(2)[active],
                                children = ["mdi-circle-slice-8"]
                            )
                        ]
                    ))                    
                
            # add the lines to the layout
            content = v.ExpansionPanelContent(children=theme_layer_widgets)
            
            # create the ep 
            ep_content.append(v.ExpansionPanel(children=[title, content]))
            
        # add the layout element to the global layout 
        self.children = ep_content
        
        return self
                
        
        
        
        
        
        
        
        
        
        