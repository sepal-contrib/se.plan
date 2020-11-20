import ipyvuetify as v 
from traitlets import observe, List, Unicode
from .. import parameter as pm
from ipywidgets import jslink
from sepal_ui import sepalwidgets as sw
from .. import message as ms
import json
from IPython import display


# for debug only 
from faker import Faker
fake = Faker()

class customize_layer_io:
    
    def __init__(self):
        
        dict_ = [
            {
                'name'   : row.layer_name,
                'assetId': row.gee_asset,
                'weight' : 0
            } for i, row in pm.layer_list.iterrows()
        ]
        
        self.layer_dict = json.dumps(dict_)

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
    
    def __init__(self):
        
        self.headers = [
          { 'text': 'Theme'     , 'value': 'theme' },
          { 'text': 'Sub theme' , 'value': 'subtheme' },
          { 'text': 'Layer name', 'value': 'name' },
          { 'text': 'Weight'    , 'value': 'weight' },
          { 'text': 'Action'    , 'value': 'action' },
        ]
        
        self.items = [
            {
                'theme'   : row.theme,
                'subtheme': row.subtheme,
                'name'    : row.layer_name,
                'weight'  : 0
            } for i, row in pm.layer_list.iterrows()
        ]
        
        self.search_field = v.TextField(
            v_model=None,
            label = 'Search',
            clearable = True,
            append_icon = 'mdi-magnify'
        )
        
        self.edit_icon = v.Icon(small=True, children=['mdi-pencil'])
        
        self.dialog_edit = v.Dialog(children = [v.Card(children = ['toto'])])
        
        super().__init__(
            v_model = [],
            show_select = True, 
            single_select = True,
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
                }
            ]
        )
        
        # link the search textField 
        self.search_field.on_event('blur', self._on_search)
        self.edit_icon.on_event('click', self._on_click)
        
        
    def _on_search(self, widget, data, event):    
        self.search = widget.v_model
        
    def _on_click(self, widget, data, event):
        
        #self.dialog_edit.value = True
        print(self.value)
        print(self.v_model)
        
        
class CustomizeLayerTile(sw.Tile):
    
    def __init__(self, io, **kwargs):
        
        # link the io to the tile
        self.io = io
        
        # name the tile
        id_ = "manual_widget"
        title = "Manual layer selection"
        
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
        
        # create the txt 
        self.txt = sw.Markdown(ms.CUSTOMIZE_TILE_TXT)
        
        # build the tile 
        super().__init__(
            id_, 
            title,
            inputs = [
                self.txt,
                self.btn_line
            ],
            **kwargs
        )
        
        # link the values to the io
        io 
        
    def apply_values(self, layers_values):
        """Apply the value that are in the layer values table. layer_values should have the exact same structure as the io define in this file"""
        
        # small check on the layer_value structure
        if len(layer_values) != len(json.loads(self.io)):
            return
        
        
        # apply the modification to the widget (the io will follow with the observe methods)
        for dict_ in layer_values:
            
            # extract the values
            name = dict_['name']
            assetId = dic_['assetId']
            weight = dict_['weight']
                    
        return 
    
class EditDialog(sw.SepalWidget, v.Dialog):
    
    def __init__(self):
        
        self.init_layer = "A/nonCustom/Layer"
        
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
            
    def _cancel_click(self, widget, data, event):
        self.value = False
        
    def _save_click(self, widget, data, event):
        self.value = False