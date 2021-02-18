from traitlets import HasTraits, Unicode
import json

from sepal_ui import sepalwidgets as sw
from ipywidgets import jslink

from component import widget as cw
        
            
class PriorityTile (sw.Tile, HasTraits):
    
    custom_v_model = Unicode().tag(sync=True)
    
    def __init__(self, **kwargs):
        
        # name the tile
        title = "Restoration priorities"
        id_ = "nested_widget"
        
        # create the sliders
        self.table = cw.PriorityTable()
        
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
        
        
        
        
        
        
        
        