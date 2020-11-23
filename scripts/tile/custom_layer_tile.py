import ipyvuetify as v 
from traitlets import observe, List, Unicode, Dict, Any
from .. import parameter as pm
from ipywidgets import jslink
from sepal_ui import sepalwidgets as sw
from .. import message as ms
import json
from IPython import display


# for debug only 
from faker import Faker
fake = Faker()

class CustomizeLayerIo:
    
    def __init__(self):
        
        self.layer_list = [
            {
                'name'   : row.layer_name,
                'layer': row.gee_asset,
                'weight' : 0
            } for i, row in pm.layer_list.iterrows()
        ]

class WeightSlider(v.Slider):
        
    _colors = {
        0: 'red',
        1: 'orange',
        2: 'yellow accent-3',
        3: 'light-green',
        4: 'green',
        5: 'primary',
        6: 'primary'
    }
    
    def __init__(self, name, default_value = 0, **kwargs):
        
        self.name = name
        
        super().__init__(
            max         = 6,
            min         = 0,
            track_color = 'grey',
            thumb_label = 'always',
            color       = self._colors[default_value],
            v_model     = default_value,
            class_      = 'ml-5 mr-5'
        )
        
    @observe('v_model')
    def on_change(self, change):
        self.color = self._colors[change['new']]
        return 
    
class LayerTable(v.DataTable, sw.SepalWidget):
    
    # unicode value to notify a change
    change_model = Any().tag(sync=True)
    
    def __init__(self):
        
        self.headers = [
          {'text': 'Theme'     , 'value': 'theme'},
          {'text': 'Sub theme' , 'value': 'subtheme'},
          {'text': 'Layer name', 'value': 'name'},
          {'text': 'Weight'    , 'value': 'weight'},
          {'text': 'Layer'     , 'value': 'layer'},
          {'text': 'Action'    , 'value': 'action'},
        ]
        
        self.items = [
            {
                'theme'   : row.theme,
                'subtheme': row.subtheme,
                'name'    : row.layer_name,
                'weight'  : 0,
                'layer'   : row.gee_asset
            } for i, row in pm.layer_list.iterrows()
        ]
        
        self.search_field = v.TextField(
            v_model=None,
            label = 'Search',
            clearable = True,
            append_icon = 'mdi-magnify'
        )
        
        self.edit_icon = v.Icon(small=True, children=['mdi-pencil'])
        
        self.dialog_edit = EditDialog()
        
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
        tmp = self.items.copy()
        
        # search for the item to modify 
        for item in tmp:
            if item['name'] == data['name']:
                item['weight'] = data['weight']
                item['layer'] = data['layer']
        
        # reply the modyfied items 
        self.items = tmp
        
        # notify the change to the rest of the app 
        self.change_model += 1
        
        return
        
        
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
        
        self.table = LayerTable()
        
        # create the txt 
        self.txt = sw.Markdown(ms.CUSTOMIZE_TILE_TXT)
        
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
    
class EditDialog(sw.SepalWidget, v.Dialog):
    
    _EMPTY_V_MODEL = { 'name': None, 'weight': None, 'layer': None }
    
    # use a custom v_model because the regular one set value automatically to 1 (display forever)
    custom_v_model = Unicode().tag(sync=True)
    
    def __init__(self):
        
        self.init_layer = ''
        self.name = ''
        
        self.title = v.CardTitle(children=['Layer name'])
        self.text = v.CardText(children = [fake.paragraph(13)])
        self.weight = WeightSlider('layer_name', 3)
        self.check_custom = v.Checkbox(v_model = False, label = 'Use custom layer')
        self.layer = v.TextField(
            clearable = True,
            v_model = self.init_layer, 
            color = 'warning',
            outlined = True,
            label = 'Layer'
        )
        
        self.ep = v.ExpansionPanels(
            accordion = True,
            children  = [
                v.ExpansionPanel(
                    key = 1,
                    children = [
                        v.ExpansionPanelHeader(
                            disable_icon_rotate = True,
                            children = ['change layer used for the computation'],
                            v_slots = [{
                                'name': 'actions',
                                'children' : v.Icon(color = 'warning', children = ['mdi-alert-circle'])
                            }]
                        ),
                        v.ExpansionPanelContent(children = [self.layer])
                    ]
                )
            ]
        )
        self.cancel = v.Btn(color='primary', outlined = True, children = ['Cancel'])
        self.save = v.Btn(color='primary', children = ['save'])        
        
        self.card = v.Card(
            children = [
                self.title,
                self.text,
                v.Subheader(children = ['Weight']),
                self.weight,
                v.Row(align_end = True, class_ = 'px-5', children = [self.ep]),
                v.CardActions( class_ = 'ma-5', children = [self.cancel, self.save])
            ]
        )
        
        super().__init__(
            custom_v_model = json.dumps(self._EMPTY_V_MODEL),
            persistent = True,
            value = False,
            max_width = '500px',
            children = [self.card]
        )
        
        # link som element together 
        self.layer.observe(self._on_layer_clear, 'v_model')
        self.cancel.on_event('click', self._cancel_click)
        self.save.on_event('click', self._save_click)
        
    def _on_layer_clear(self, change):
        if not change['new']:
            change['owner'].v_model = self.init_layer
            
        return 
            
    def _cancel_click(self, widget, data, event):
        
        # close without doing anything
        self.value = False
        
        return 
        
    def _save_click(self, widget, data, event):
        
        # change v_model with the new values
        tmp = json.loads(self.custom_v_model)
        tmp.update(
            name   = self.name,
            weight = self.weight.v_model,
            layer  = self.layer.v_model
        )
        self.custom_v_model = json.dumps(tmp)
        
        # close 
        self.value = False
        
        return
        
    def set_dialog(self, data):
        
        # if data are empty
        if not len(data):
            
            # default title
            self.title.children = ['No layer']
            
            # default text
            self.text.children = ['You need to select a layer before making modifications']
            
            # mute all the component 
            self.weight.v_model = 3
            self.weight.disabled = True
            
            self.layer.v_model = 'no Layer'
            self.layer.disabled = True
            
            # disable save 
            self.save.disabled = True
            
        else: 
            
            # change title 
            self.name = data[0]['name']
            self.title.children = [data[0]['name']]
            
            # change text 
            layer_df_line = pm.layer_list[pm.layer_list.layer_name == data[0]['name']].iloc[0]
            self.text.children = [layer_df_line.layer_info]
            
            # enable slider 
            self.weight.disabled = False
            self.weight.v_model = data[0]['weight']
            
            # enable textField
            self.layer.disabled = False
            self.layer.v_model = data[0]['layer']
            
            # change default layer name 
            self.init_layer = layer_df_line.gee_asset
            
            # enable save 
            self.save.disabled = False
            
        return