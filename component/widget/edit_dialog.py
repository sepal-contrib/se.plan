from traitlets import Unicode
import json

from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
import ipyvuetify as v
from faker import Faker
import pandas as pd

from component import parameter as cp
from component.message import cm
from .weight_slider import WeightSlider

fake = Faker()

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
        self.check_custom = v.Checkbox(v_model = False, label = cm.dial.layer)
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
                            children = [cm.dial.change],
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
        
        self.m = sm.SepalMap()
        self.m.layout.height = '40vh'
        self.m.layout.margin = '2em'
        
        self.cancel = v.Btn(color='primary', outlined = True, children = [cm.dial.cancel])
        self.save = v.Btn(color='primary', children = [cm.dial.save])        
        
        self.card = v.Card(
            children = [
                self.title,
                self.text,
                v.Subheader(children = [cm.dial.weight]),
                self.weight,
                v.Row(align_end = True, class_ = 'px-5', children = [self.ep]),
                self.m,
                v.CardActions( class_ = 'ma-5', children = [self.cancel, self.save])
            ]
        )
        
        super().__init__(
            custom_v_model = json.dumps(self._EMPTY_V_MODEL),
            persistent = True,
            value = False,
            max_width = '700px',
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
            self.title.children = [cm.dial.no_layer]
            
            # default text
            self.text.children = [cm.dial.disc]
            
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
            
            # get the layer list pd dataframe 
            layer_list = pd.read_csv(cp.layer_list).fillna('')
            
            # change text 
            layer_df_line = layer_list[layer_list.layer_name == data[0]['name']].iloc[0]
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