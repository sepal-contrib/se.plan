from pathlib import Path
import json

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
import ee

from component import widget as cw
from component.message import cm
from component import scripts as cs
from component import parameter as cp

ee.Initialize()


class CustomizeLayerTile(sw.Tile):
    def __init__(self, aoi_tile, model, questionnaire_model, **kwargs):

        # link the ios to the tile
        self.model = model
        self.questionnaire_model = questionnaire_model
        self.aoi_tile = aoi_tile

        self.table = cw.LayerTable(aoi_tile)

        # create the txt
        self.txt = sw.Markdown(cm.custom.desc)

        self.reset_to_recipe = sw.Btn(
            text=cm.custom.recipe.apply,
            icon="mdi-download",
            class_="ml-2",
            color="success",
        )

        # build the tile
        super().__init__(
            "manual_widget", cm.custom.title, inputs=[self.txt, self.table], **kwargs
        )

        # js behaviours
        self.table.observe(self._on_item_change, "change_model")

    def _on_item_change(self, change):

        # normally io and the table have the same indexing so I can take advantage of it
        for i in range(len(self.model.layer_list)):
            io_item = self.model.layer_list[i]
            item = self.table.items[i]

            io_item["layer"] = item["layer"]
            io_item["unit"] = item["unit"]

        return self

    def apply_values(self, layers_values):
        """Apply the value that are in the layer values table. layer_values should have the exact same structure as the io define in this file"""

        # small check on the layer_value structure
        if len(layers_values) != len(self.model.layer_list):
            return

        # create a tmp list of items
        # update it with the current values in self.table.items
        tmp_table = []
        for i, item in enumerate(self.table.items):
            tmp_table.append({})
            for k in item.keys():
                tmp_table[i][k] = item[k]

        # apply the modification to the widget (the io will follow with the observe methods)
        for i, dict_ in enumerate(layers_values):

            # apply them to the table
            if tmp_table[i]["name"] == dict_["name"]:
                tmp_table[i].update(layer=dict_["layer"], unit=dict_["unit"])

        # change the actual value of items
        self.table.items = tmp_table

        # notify the change to rest of the app
        self.table.change_model += 1

        return self
