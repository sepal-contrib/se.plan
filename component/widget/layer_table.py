import json
from traitlets import Any

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
import pandas as pd

from component import parameter as cp
from .edit_dialog import EditDialog

class LayerTable(v.DataTable, sw.SepalWidget):
    
    # unicode value to notify a change
    change_model = Any().tag(sync=True)
    
    def __init__(self, aoi_tile):
        
        self.headers = [
            {'text': 'Theme'     , 'value': 'theme'},
            {'text': 'Subtheme'  , 'value': 'subtheme'},
            {'text': 'Layer name', 'value': 'name'},
            {'text': 'Layer'     , 'value': 'layer'},
            {'text': 'Unit'      , 'value': 'unit'},
            {'text': 'Action'    , 'value': 'action'},
        ]
        
        self.items = [
            {
                'theme'   : row.theme,
                'subtheme': row.subtheme,
                'name'    : row.layer_name,
                'layer'   : row.gee_asset,
                'unit'    : row.unit
            } for i, row in pd.read_csv(cp.layer_list).fillna('').iterrows()
        ]
        
        self.search_field = v.TextField(
            v_model=None,
            label = 'Search',
            clearable = True,
            append_icon = 'mdi-magnify'
        )
        
        self.edit_icon = v.Icon(small=True, children=['mdi-pencil'])
        
        self.dialog_edit = EditDialog(aoi_tile)
        
        super().__init__(
            change_model = 0,
            v_model = [],
            show_select = True, 
            single_select = True,
            item_key = 'name',
            headers = self.headers,
            items = self.items,
            search = '',
            v_slots = [
                { # the search slot 
                    'name': 'top',
                    'variable': 'data-table',
                    'children': self.search_field
                },
                { # the pencil for modification
                    'name': 'item.action',
                    'variable': 'item',
                    'children': self.edit_icon
                },
                { # the dialog as a footer
                    'name': 'footer',
                    'children': self.dialog_edit
                }
            ]
        )
        
        # link the search textField 
        self.search_field.on_event('blur', self._on_search)
        self.edit_icon.on_event('click', self._on_click)
        self.dialog_edit.observe(self._on_dialog_change, 'custom_v_model')
        
        
    def _on_search(self, widget, data, event):    
        self.search = widget.v_model
        
        return 
        
    def _on_click(self, widget, data, event):
        
        self.dialog_edit.set_dialog(self.v_model)
        self.dialog_edit.value = True
        
        return
    
    def _on_dialog_change(self, change):
        
        data = json.loads(change['new'])
        
        # we need to change the full items traitlet to trigger a change 
        # create a tmp list of items
        # update it with the current values in self.table.items
        tmp_table = []
        for i, item in enumerate(self.items):
            tmp_table.append({})
            for k in item.keys():
                tmp_table[i][k] = item[k]
        
        # search for the item to modify 
        for item in tmp_table:
            if item['name'] == data['name']:
                item.update(
                    layer = data['layer'],
                    unit = data['unit']
                )
        
        # reply with the modyfied items 
        self.items = tmp_table
        
        # notify the change to the rest of the app 
        self.change_model += 1
        
        # deselect the item 
        # this trick is to force the update of the values at the next selection
        # still searching for a more elegant solution
        self.v_model = []
        
        return