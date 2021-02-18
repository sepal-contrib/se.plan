import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from traitlets import Unicode, HasTraits
from .. import parameter as pm 
from .. import message as ms
import json
from ipywidgets import jslink
        
            
class PriorityTile (sw.Tile, HasTraits):
    
    custom_v_model = Unicode().tag(sync=True)
    
    def __init__(self, **kwargs):
        
        # name the tile
        title = "Restoration priorities"
        id_ = "nested_widget"
        
        # create the sliders
        self.table = PriorityTable()
        
        # build the tile
        super().__init__(
            id_, 
            title, 
            inputs = [self.table],
            **kwargs
        )
        
        self.v_model = json.dumps(self.table._DEFAULT_V_MODEL)
        
        # hide the borders 
        self.children[0].elevation = 0
        
        #link the widgets to the tile 
        jslink((self, 'v_model'),(self.table, 'v_model'))
        
        
        
        
        
        
        
        