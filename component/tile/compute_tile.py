from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component import scripts as cs
from component.message import cm
from component import widget as cw
from component import parameter as cp

class ValidationTile(sw.Tile):
    
    def __init__(self, aoi_tile, questionnaire_tile, layer_tile):
        
        # gather the io 
        self.layer_io = layer_tile.io
        self.aoi_io = aoi_tile.io
        self.question_io = questionnaire_tile.io
        
        # gather the tiles that need to be filled
        self.layer_tile = layer_tile
        self.aoi_tile = aoi_tile
        self.questionnaire_tile = questionnaire_tile
        
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
        self.reset_to_recipe.on_event('click', self.load_recipe)
        
    def _validate_data(self, widget, event, data):
        """validate the data and release the computation btn"""
        
        widget.toggle_loading()
    
        # watch the inputs
        self.layers_recipe.digest_layers(self.layer_io, self.question_io)
        self.layers_recipe.show()
        
        # save the inputs in a json
        cs.save_recipe(self.layer_io, self.aoi_io, self.question_io)
    
        widget.toggle_loading()
        
        return self
    
    def load_recipe(self, widget, event, data, path=None):
        """load the recipe file into the different io, then update the display of the table"""
        
        # toogle the btns
        widget.toggle_loading()

        # check if path is set, if not use the one frome file select 
        path = path or self.file_select.v_model
        
        try:
            
            cs.load_recipe(self.layer_tile, self.aoi_tile, self.questionnaire_tile, path)

            # automatically validate them 
            self.btn.fire_event('click', None)

            self.recipe_output.add_msg('loaded', 'success')

        except Exception as e:
            self.recipe_output.add_msg(str(e), 'error')

        # toogle the btns
        widget.toggle_loading()

        return self