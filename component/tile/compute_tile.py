from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component import scripts as cs
from component.message import cm
from component import widget as cw
from component import parameter as cp

class ValidationTile(sw.Tile):
    
    def __init__(self, io, aoi_io):#, compute_tile):
        
        # gather the io 
        self.io = io
        self.aoi_io = aoi_io
        #self.compute_tile = compute_tile
        
        # create the layer list widget 
        self.layers_recipe = cw.layerRecipe().hide()
        mkd = sw.Markdown('  \n'.join(cm.valid.txt))
        
        # add the btn and output 
        self.valid = sw.Btn(cm.valid.display, class_ = 'ma-1')
        self.output = sw.Alert()
        
        # add the recipe loader
        self.reset_to_recipe = sw.Btn(text=cm.custom.recipe.apply,icon='mdi-download', class_='ml-2')
        self.file_select = sw.FileInput(['.json'], cp.result_dir, cm.custom.recipe.file)
        self.recipe_output = sw.Alert()
        ep = v.ExpansionPanels(class_="mt-5", children=[v.ExpansionPanel(children=[
            v.ExpansionPanelHeader(
                disable_icon_rotate = True,
                children=[cm.custom.recipe.title],
                v_slots = [{
                    'name': 'actions',
                    'children' : v.Icon(children=['mdi-download'])
                }]
            ),
            v.ExpansionPanelContent(children=[self.file_select, self.reset_to_recipe, self.recipe_output])
        ])])
        
        # create the tile 
        super().__init__(
            id_ = "compute_widget",
            inputs= [ep, mkd, self.layers_recipe],
            title = cm.valid.title,
            btn = sw.Btn(cm.valid.display, class_ = 'ma-1'),
            output = self.output
        )
        
        # js behaviours 
        self.btn.on_event('click', self._validate_data)
        #self.reset_to_recipe.on_event('click', self.load_recipe)
        
    def _validate_data(self, widget, event, data):
        """validate the data and release the computation btn"""
        
        widget.toggle_loading()
    
        # watch the inputs
        self.layers_recipe.digest_layers(self.io.layer_list)
        self.layers_recipe.show()
        
        # save the inputs in a json
        cs.save_recipe(self.io, self.aoi_io)
    
        # free the computation btn
        #self.compute_tile.btn.disabled = False
    
        widget.toggle_loading()
        
        return self
    
    #def load_recipe(self, widget, event, data, path=None):
    #    """load the recipe file into the different io, then update the display of the table"""
#
    #    # toogle the btns
    #    self.reset_to_questionnaire.toggle_loading()
    #    widget.toggle_loading()
#
    #    # check if path is set, if not use the one frome file select 
    #    path = path or self.file_select.v_model
#
    #    try:
    #        cs.load_recipe(self.io, self.aoi_tile.io, path)
#
    #        # reload the values in the table
    #        self.apply_values(self.io.layer_list)
#
    #        # validate the aoi 
    #        self.aoi_tile.aoi_select_btn.fire_event('click','')
#
    #        self.recipe_output.add_msg('loaded', 'success')
#
    #    except Exception as e:
    #        self.recipe_output.add_msg(str(e), 'error')
#
    #    # toogle the btns
    #    self.reset_to_questionnaire.toggle_loading()
    #    widget.toggle_loading()
#
    #    return self
    
#class ComputeTile(sw.Tile):
#    
#    def __init__(self, io, default_io, aoi_io, m, questionaire_io, rp_geeio):
#        
#        # gather the ios 
#        self.io = io
#        self.default_io = default_io
#        self.aoi_io = aoi_io
#        self.questionaire_io = questionaire_io
#        self.geeio = rp_geeio
#        
#        # get the map
#        self.m = m
#        
#        # add the widgets 
#        compute_txt = sw.Markdown(cm.compute.desc)
#        
#        self.btn = sw.Btn(cm.compute.btn, disabled=True)
#        self.output = sw.Alert()
#        
#        # create the tile 
#        super().__init__(
#            id_ = "compute_widget",
#            title = cm.compute.title,
#            inputs = [compute_txt],
#            btn = self.btn,
#            output = self.output
#        )
#        
#        # add the js behaviours 
#        self.btn.on_event('click', self._compute)
#        
#    def _compute(self, widget, data, event):
#        """compute the restoration plan and display both the maps and the dashboard content"""
#    
#        widget.toggle_loading()
#    
#        # create a layer and a dashboard 
#        layer = self.geeio.wlc()
#        # setattr(self, geeio, geeio)
#        # display the layer in the map
#        # layer = wlcoutputs[0]
#        cs.display_layer(layer, self.aoi_io, self.m)
#        
#        # add the possiblity to draw on the map and release the compute dashboard btn
#        self.m.show_dc()
#        
#        # display the dashboard 
#        # self.area_tile.set_summary(dashboard) # calling it without argument will lead to fake output
#        # self.theme_tile.dev_set_summary(dashboard) # calling it without argument will lead to fake output
#    
#        widget.toggle_loading()
#        
#        return self