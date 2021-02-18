from sepal_ui import sepalwidgets as sw 
import ipyvuetify as v

from component import widget as cw
from component.message import cm
        
class CustomizeLayerTile(sw.Tile):
    
    def __init__(self, io, **kwargs):
        
        # link the io to the tile
        self.io = io
        
        # name the tile
        id_ = "manual_widget"
        title = "Customize layers input"
        
        # create the btns
        self.reset_to_questionnaire = sw.Btn(
            text   = 'Apply questionnaire answers', 
            icon   = 'mdi-file-question-outline',
            class_ = 'ml-5 mr-2'
        )
        self.reset_to_questionnaire.color = 'success'
        
        self.reset_to_default = sw.Btn(
            text   = 'Apply default parameters',
            icon   = 'mdi-restore', 
            class_ = 'ml-2'
        )
        self.reset_to_default.color = 'warning'
        
        self.btn_line = v.Row(
            class_   = 'mb-3',
            children = [self.reset_to_questionnaire, self.reset_to_default]
        )
        
        self.table = cw.LayerTable()
        
        # create the txt 
        self.txt = sw.Markdown(cm.questionnaire.custom_tile_txt)
        
        # build the tile 
        super().__init__(
            id_, 
            title,
            inputs = [
                self.txt,
                self.btn_line,
                self.table
            ],
            **kwargs
        )
        
        # link the values to the io
        self.table.observe(self._on_item_change, 'change_model')
        
    def _on_item_change(self, change):
            
        # normally io and the table have the same indexing so I can take advantage of it 
        for i in range (len(self.io.layer_list)):
            io_item = self.io.layer_list[i]
            item = self.table.items[i]
            
            io_item['layer'] = item['layer']
            io_item['weight'] = item['weight']
            
        return
        
    def apply_values(self, layers_values):
        """Apply the value that are in the layer values table. layer_values should have the exact same structure as the io define in this file"""
        
        # small check on the layer_value structure
        if len(layers_values) != len(self.io.layer_list):
            return
        
        # apply the modification to the widget (the io will follow with the observe methods)
        for i, dict_ in enumerate(layers_values):
            
            # apply them to the table
            if self.table.items[i]['name'] == dict_['name']:
                self.table.items[i].update(
                    layer  = dict_['layer'],
                    weight = dict_['weight']
                )
                
            # notify the change to rest of the app 
            self.table.change_model += 1
                     
        return 