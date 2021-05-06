from pathlib import Path 
import json 

from sepal_ui import sepalwidgets as sw 
import ipyvuetify as v
import ee 

from component import widget as cw
from component.message import cm
from component import io as cio
from component import scripts as cs
from component import parameter as cp

ee.Initialize()
        
class CustomizeLayerTile(sw.Tile):
    
    def __init__(self, aoi_tile, io, questionnaire_io, **kwargs):
        
        # link the ios to the tile
        self.io = io
        self.questionnaire_io = questionnaire_io
        self.aoi_tile = aoi_tile
        
        # create the btns
        self.reset_to_questionnaire = sw.Btn(
            text   = cm.custom.question_btn, 
            icon   = 'mdi-file-question-outline',
            class_ = 'ml-5 mr-2',
            color = 'success'
        )
        
        self.btn_line = v.Row(
            class_   = 'mb-3',
            children = [self.reset_to_questionnaire]
        )
        
        self.table = cw.LayerTable(aoi_tile)
        
        # create the txt 
        self.txt = sw.Markdown(cm.custom.desc)
        
        # create the panel that contains the file loader 
        self.file_select = sw.FileInput(['.json'], cp.result_dir, cm.custom.recipe.file)

        self.reset_to_recipe = sw.Btn(
            text   = cm.custom.recipe.apply,
            icon   = 'mdi-download', 
            class_ = 'ml-2',
            color = 'success'
        )

        self.recipe_output = sw.Alert()

        ep = v.ExpansionPanels(class_="mt-5", children=[v.ExpansionPanel(children=[
            v.ExpansionPanelHeader(
                disable_icon_rotate = True,
                children=[cm.custom.recipe.title],
                v_slots = [{
                    'name': 'actions',
                    'children' : v.Icon(children=['mdi-download'])
                }]
            ),
            v.ExpansionPanelContent(children=[self.file_select, self.reset_to_recipe, self.recipe_output])
        ])])
        
        # build the tile 
        super().__init__(
            "manual_widget", 
            cm.custom.title,
            inputs = [
                ep,
                self.txt,
                self.btn_line,
                self.table
            ],
            **kwargs
        )
        
        # js behaviours
        self.table.observe(self._on_item_change, 'change_model')
        self.reset_to_questionnaire.on_event('click', self._apply_questionnaire)
        self.reset_to_recipe.on_event('click', self.load_recipe)
        
    def _on_item_change(self, change):
            
        # normally io and the table have the same indexing so I can take advantage of it 
        for i in range (len(self.io.layer_list)):
            io_item = self.io.layer_list[i]
            item = self.table.items[i]
            
            io_item['layer'] = item['layer']
            io_item['unit'] = item['unit']
            io_item['weight'] = item['weight']
            
        return self
        
    def apply_values(self, layers_values):
        """Apply the value that are in the layer values table. layer_values should have the exact same structure as the io define in this file"""
        
        # small check on the layer_value structure
        if len(layers_values) != len(self.io.layer_list):
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
            if tmp_table[i]['name'] == dict_['name']:
                tmp_table[i].update(
                    layer = dict_['layer'],
                    weight = dict_['weight'],
                    unit = dict_['unit']
                )
            
        # change the actual value of items 
        self.table.items = tmp_table
            
        # notify the change to rest of the app 
        self.table.change_model += 1
                     
        return self
    
    def _apply_questionnaire(self, widget, event, data):
        """apply the answer to the questionnaire to the datatable"""
        
        # toggle the btns
        widget.toggle_loading()

        self.reset_to_questionnaire.toggle_loading()
    
        # process the questionnaire to produce a layer list 
        layers_values = cs.compute_questionnaire(self.questionnaire_io)
        self.apply_values(layers_values)
    
        # manually change the items
        # for no reason the display items doesn't upload programatically
        new_items = self.table.items.copy()
        self.table.items = new_items
    
        # toggle the btns
        widget.toggle_loading()

        self.reset_to_questionnaire.toggle_loading()
    
        return self 
    
    def load_recipe(self, widget, event, data, path=None):
        """load the recipe file into the different io, then update the display of the table"""

        # toogle the btns
        self.reset_to_questionnaire.toggle_loading()
        widget.toggle_loading()

        # check if path is set, if not use the one frome file select 
        path = path or self.file_select.v_model

        try:
            cs.load_recipe(self.io, self.aoi_tile.io, path)

            # reload the values in the table
            self.apply_values(self.io.layer_list)

            # validate the aoi 
            self.aoi_tile.aoi_select_btn.fire_event('click','')

            self.recipe_output.add_msg('loaded', 'success')

        except Exception as e:
            self.recipe_output.add_msg(str(e), 'error')

        # toogle the btns
        self.reset_to_questionnaire.toggle_loading()
        widget.toggle_loading()

        return self