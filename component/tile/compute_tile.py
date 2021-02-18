from sepal_ui import sepalwidgets as sw

from component import scripts as cs
from component.message import cm

class ValidationTile(sw.Tile):
    
    def __init__(self, io, aoi_io, compute_tile):
        
        # gather the io 
        self.io = io
        self.aoi_io = aoi_io
        self.compute_tile = compute_tile
        
        # create the tile 
        super().__init__(
            id_ = compute_tile._metadata['mount_id'],
            title = cm.valid.title,
            btn = sw.Btn(cm.valid.btn),
            output = sw.Alert()
        )
        
        # js behaviours 
        self.btn.on_event('click', self._validate_data)
        
    def _validate_data(self, widget, event, data):
        """validate the data and release the computation btn"""
        
        widget.toggle_loading()
    
        # watch the inputs
        cs.sum_up(self.aoi_io, self.io, self.output)
    
        # free the computation btn
        self.compute_tile.btn.disabled = False
    
        widget.toggle_loading()
        
        return self
    
class ComputeTile(sw.Tile):
    
    def __init__(self, io, aoi_io, m, dashboard_tile):
        
        # gather the ios 
        self.io = io
        self.aoi_io = aoi_io
        
        # get the map
        self.m = m
        
        # get the dashboard tile 
        self.dashboard_tile = dashboard_tile
        
        # add the widgets 
        compute_txt = sw.Markdown(cm.compute.desc)
        
        # create the tile 
        super().__init__(
            id_ = "compute_widget",
            title = cm.compute.title,
            inputs = [compute_txt],
            btn = sw.Btn(cm.compute.btn, disabled = True),
            output = sw.Alert()
        )
        
        # add the js behaviours 
        self.btn.on_event('click', self._compute)
        
    def _compute(self, widget, data, event):
        """compute the restoration plan and display both the maps and the dashboard content"""
    
        widget.toggle_loading()
    
        # create a layer and a dashboard 
        layer, dashboard = cs.compute_layers(self.io)
    
        # display the layer in the map
        cs.display_layer(layer, self.aoi_io, self.m)
        
        # display the dashboard 
        self.dashboard_tile.set_content([dashboard])
    
        widget.toggle_loading()
        
        return self