from datetime import datetime as dt
from pathlib import Path

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw 
from sepal_ui.scripts import gee
import ee 

from component.message import cm
from component import scripts as cs
from component import parameter as cp

ee.Initialize()

class ExportMap(v.Menu, sw.SepalWidget):
    
    def __init__(self):
        
        # init the downloadable informations
        self.geometry = None
        self.dataset = None
        self.name = None
        
        # create the useful widgets 
        self.w_scale = v.Slider(
            v_model=30, #align on the landsat images
            min=10, 
            max=300, 
            thumb_label=True,
            step = 10
        )
        
        self.w_method = v.RadioGroup(
            v_model='gee',
            row=True,
            children=[
                v.Radio(label=cm.export.radio.sepal, value='sepal'),
                v.Radio(label=cm.export.radio.gee, value='gee')
            ]
        )
        
        self.alert = sw.Alert()
        
        #self.w_cancel = sw.Btn(cm.export.cancel, outlined=True, small=True)
        self.w_apply = sw.Btn(cm.export.apply, small=True)
        
        export_data = v.Card(
            children = [
                v.CardTitle(children=[v.Html(tag='h4', children=[cm.export.title])]),
                v.CardText(children=[
                    v.Html(tag="h4", children=[cm.export.scale]),
                    self.w_scale,
                    v.Html(tag="h4", children=[cm.export.radio.label]),
                    self.w_method,
                    self.alert
                ]),
                v.CardActions(children=[
                    #self.w_cancel, 
                    self.w_apply
                ])
            ]
        )

        # the clickable icon
        self.btn = v.Btn(
            v_on='menu.on', 
            color='primary', 
            icon = True, 
            children=[v.Icon(children=['mdi-cloud-download'])]
        )
        
        super().__init__(
            value=False,
            close_on_content_click = False,
            nudge_width = 200,
            offset_x=True,
            children = [export_data],
            v_slots = [{
                'name': 'activator',
                'variable': 'menu',
                'children': self.btn
            }]
        )
        
        # add js behaviour 
        #self.w_cancel.on_event('click', self._cancel)
        self.w_apply.on_event('click', self._apply)
        
    def set_data(self, dataset, geometry, name=None):
        """set the dataset and the geometry to allow the download"""
        
        self.geometry = geometry
        self.dataset = dataset
        self.name = name
        
        return self
    
    def _cancel(self, widget, event, data):
        "close the menu and do nothing"
        
        self.value = False
        
        return self
    
    def _apply(self, widget, event, data):
        """download the dataset using the given parameters"""
        
        #print(self.dataset)
        #print(self.geometry)
        
        folder = Path(ee.data.getAssetRoots()[0]['id'])
        
        # check if a dataset is existing
        if self.dataset == None or self.geometry == None:
            print('toto')
            return self
        
        # set the parameters
        name = self.name or dt.now().strftime("%Y-%m-%d_%H-%M-%S")
        export_params = {
            'image': self.dataset,
            'description': name,
            'scale': self.w_scale.v_model,
            'region': self.geometry
        }
        
        # launch the task 
        if self.w_method.v_model == 'gee':
            export_params.update(assetId=str(folder/name))
            task = ee.batch.Export.image.toAsset(**export_params)
            task.start()
            self.alert.add_msg("the task have been launched in your GEE acount", "success")
            
        elif self.w_method.v_model == 'sepal':
            
            gdrive = cs.gdrive()
            
            files = gdrive.get_files(name)
            if files == []:
                task = ee.batch.Export.image.toDrive(**export_params)
                task.start()
                gee.wait_for_completion(name, self.alert)
                files = gdrive.get_files(name)
                
            gdrive.download_files(files, cp.result_dir)
            gdrive.delete_files(files)
            self.alert.add_msg("map exported", "success")
            
        return self
        
        
        