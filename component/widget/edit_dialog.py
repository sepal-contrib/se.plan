from traitlets import Unicode
import json

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
from faker import Faker

from component import parameter as cp

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
            layer_df_line = cp.layer_list[cp.layer_list.layer_name == data[0]['name']].iloc[0]
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