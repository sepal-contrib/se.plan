from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component import scripts as cs
from component.message import cm
from component import widget as cw

class ValidationTile(sw.Tile):
    
    def __init__(self, io, aoi_io, compute_tile):
        
        # gather the io 
        self.io = io
        self.aoi_io = aoi_io
        self.compute_tile = compute_tile
        
        # create the layer list widget 
        self.layers_recipe = cw.layerRecipe()
        mkd = sw.Markdown('  \n'.join(cm.valid.txt))
        
        # add the btn and output 
        self.valid = sw.Btn(cm.valid.display, class_ = 'ma-1')
        self.save = sw.Btn(cm.valid.save, class_ = 'ma-1', disabled = True)
        self.output = sw.Alert()
        
        # create the tile 
        super().__init__(
            id_ = compute_tile._metadata['mount_id'],
            inputs= [self.layers_recipe, mkd],
            title = cm.valid.title,
            btn = v.Row(children = [self.valid, self.save]),
            output = self.output
        )
        
        # js behaviours 
        self.valid.on_event('click', self._validate_data)
        
    def _validate_data(self, widget, event, data):
        """validate the data and release the computation btn"""
        
        widget.toggle_loading()
    
        # watch the inputs
        #cs.sum_up(self.aoi_io, self.io, self.output)
        self.layers_recipe.digest_layers(self.io.layer_list)
    
        # free the computation btn
        self.compute_tile.btn.disabled = False
        self.save.disabled = False
    
        widget.toggle_loading()
        
        return self
    
class ComputeTile(sw.Tile):
    
    def __init__(self, io, aoi_io, m, area_tile, theme_tile, questionaire_io):
        
        # gather the ios 
        self.io = io
        self.aoi_io = aoi_io
        self.questionaire_io = questionaire_io
        
        # get the map
        self.m = m
        
        # get the dashboard tile 
        self.area_tile = area_tile
        self.theme_tile = theme_tile
        
        # add the widgets 
        compute_txt = sw.Markdown(cm.compute.desc)
        
        self.btn = sw.Btn(cm.compute.btn, disabled=True)
        self.output = sw.Alert()
        
        # create the tile 
        super().__init__(
            id_ = "compute_widget",
            title = cm.compute.title,
            inputs = [compute_txt],
            btn = self.btn,
            output = self.output
        )
        
        # add the js behaviours 
        self.btn.on_event('click', self._compute)
        
    def _compute(self, widget, data, event):
        """compute the restoration plan and display both the maps and the dashboard content"""
    
        widget.toggle_loading()
    
        # create a layer and a dashboard 
        layer, dashboard = cs.compute_layers(self.aoi_io, self.io, self.questionaire_io)
    
        # display the layer in the map
        cs.display_layer(layer, self.aoi_io, self.m)
        
        # display the dashboard 
        self.area_tile.set_summary() # calling it without argument will lead to fake output
        self.theme_tile.set_summary() # calling it without argument will lead to fake output
    
        widget.toggle_loading()
        
        return self