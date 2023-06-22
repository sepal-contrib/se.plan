import json

import ipyvuetify as v
import pandas as pd
from sepal_ui import sepalwidgets as sw

from component import parameter as cp
from component import widget as cw
from component.message import cm


class layerRecipe(v.ExpansionPanels, sw.SepalWidget):
    # load the layers
    LAYER_LIST = pd.read_csv(cp.layer_list).fillna("")
    LAYER_LIST = LAYER_LIST.rename(columns={"gee_asset": "layer", "layer_name": "name"})
    LAYER_LIST["weight"] = [0 for i in range(len(LAYER_LIST))]

    def __init__(self):
        super().__init__(class_="mt-5 mb-5", accordion=True, focusable=True)

        # display the default values (all with default layer and 0 valued weight)
        self.digest_layers()

    def digest_layers(self, layer_model=None, question_model=None):
        """Digest the layers as a json list.

        This list should be composed of at least 6 information : id, name, layer, theme and subtheme
        When digestion, the layout will represent each layer sorted by categories
        fore each one of them if the layer used is the default one we'll write default, if not the name of the layer.
        for each one of them the value of the weight will also be set.
        """
        # exit if models are not set
        if any([layer_model is None, question_model is None]):
            return self

        # read the json str into a panda dataframe
        layer_list = layer_model.layer_list
        layer_list = pd.DataFrame(layer_list) if layer_list else self.LAYER_LIST

        ep_content = []
        for theme in cp.themes:
            # filter the layers
            tmp_layers = layer_list[layer_list.theme == theme]

            # add the theme title
            title = v.ExpansionPanelHeader(children=[theme.capitalize()])

            # loop in these layers and create the widgets
            theme_layer_widgets = []
            for id_, asset in zip(tmp_layers.id, tmp_layers.layer):
                # get the asset name as displayed in the hints
                original_row = self.LAYER_LIST[self.LAYER_LIST.layer_id == id_]
                original_asset = original_row["layer"].squeeze()
                is_same = asset == original_asset
                asset_name = cm.compute.default_label if is_same else asset

                # get the name of the layer
                name = getattr(cm.layers, id_).name

                # cannot make the slots work with icons so I need to move to intermediate layout
                if theme == "benefit":
                    # get the informations to display from questionnaire
                    weight = json.loads(question_model.priorities)[id_]
                    color = cp.gradient(5)[weight]
                    icon = f"mdi-numeric-{weight}-circle"

                elif theme == "cost":
                    # get the informations to display from questionnaire
                    color = cp.gradient(2)[1]  # always true
                    icon = "mdi-circle-slice-8"

                elif id_ not in ["ecozones", "land_cover", "treecover_with_potential"]:
                    # get the informations to display from questionnaire
                    active = json.loads(question_model.constraints)[id_] != -1
                    color = cp.gradient(2)[active]
                    icon = "mdi-circle-slice-8"

                # create the widget
                w_text = cw.RecipeTextField(color, name, asset_name)
                w_icon = cw.RecipeIcon(color, icon)
                w_row = sw.Row(class_="ml-2 mr_2", children=[w_text, w_icon])
                theme_layer_widgets.append(w_row)

            # add the lines to the layout
            content = v.ExpansionPanelContent(children=theme_layer_widgets)

            # create the ep
            ep_content.append(v.ExpansionPanel(children=[title, content]))

        # add the layout element to the global layout
        self.children = ep_content

        return self
