from traitlets import Unicode
import json

from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
import ipyvuetify as v
from faker import Faker
import pandas as pd
import ee

from component import parameter as cp
from component.message import cm
from .weight_slider import WeightSlider

fake = Faker()
ee.Initialize()

class EditDialog(sw.SepalWidget, v.Dialog):
    
    _EMPTY_V_MODEL = { 'name': None, 'weight': None, 'layer': None }
    
    # use a custom v_model because the regular one set value automatically to 1 (display forever)
    custom_v_model = Unicode().tag(sync=True)
    
    def __init__(self, aoi_tile):
        
        # listen to the aoi_tile to update the map
        self.tile = aoi_tile
        
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
        
        self.ep = v.ExpansionPanels(accordion = True, children = [
            v.ExpansionPanel(children = [
                v.ExpansionPanelHeader(
                    disable_icon_rotate = True,
                    children = [cm.dial.change],
                    v_slots = [{
                        'name': 'actions',
                        'children' : v.Icon(color = 'warning', children = ['mdi-alert-circle'])
                    }]
                ),
                v.ExpansionPanelContent(children = [self.layer])
            ])
        ])
        
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
        
        # link some element together 
        self.layer.observe(self._on_layer_change, 'v_model')
        self.cancel.on_event('click', self._cancel_click)
        self.save.on_event('click', self._save_click)
        self.tile.aoi_select_btn.observe(self._update_aoi, 'loading')
        
    def _on_layer_change(self, change):
        
        # do nothing if it's no_layer
        if change['new'] == 'no Layer':
            return self
        
        # replace the v_model by the init one 
        if not change['new']:
            change['owner'].v_model = self.init_layer
        
        # if the layer is different than the init one
        elif change['new'] != self.init_layer:
            
            # check if the layer is quantile based 
            
            # display it on the map
            self.m.addLayer(
                ee.Image(change['new']).clip(self.tile.io.get_aoi_ee()),
                cp.final_viz.update(max=5),
                'custom layer'
            )
            
        return self
            
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
    
    def _update_aoi(self, change):
        
        # the toggle btn has changed let's see if it's for a good reason
        if self.tile.aoi_output.type == 'success':
            
            # get the aoi
            aoi_ee = self.tile.io.get_aoi_ee()
            
            # draw an outline 
            outline = ee.Image().byte().paint(
              featureCollection =  aoi_ee,
              color = 1,
              width = 3
            )
            
            # update the map
            self.m.addLayer(outline, {'palette': v.theme.themes.dark.accent[1:]}, 'aoi')
            self.m.zoom_ee_object(aoi_ee.geometry())
            
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
            
            # remove the images 
            for l in self.m.layers:
                if l.name in ['init layer', 'custom layer']:
                    self.m.remove_layer(l)
            
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
            
            # update the map with the default layer
            self.m.addLayer(
                ee.Image(self.init_layer).clip(self.tile.io.get_aoi_ee()),
                cp.final_viz.update(max=5),
                'init layer'
            )
            
            # add the custom layer if existing 
            if data[0]['layer'] != self.init_layer:
                self.m.addLayer(
                    ee.Image(data[0]['layer']).clip(self.tile.io.get_aoi_ee()),
                    cp.final_viz.update(max=5),
                    'custom_layer'
                )
            
            # enable save 
            self.save.disabled = False
            
        return