from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
from .. import message as ms
from .. import parameter as pm


class Potential_tile(sw.Tile):
    
    def __init__(self, **kwargs):
        
        # name the tile 
        title = "Restoration potential and land use" 
        id_ = 'nested_widget'
        
        # short description of the tile
        tile_txt = sw.Markdown(ms.POTENTIAL_TXT)
        
        # select the potential land use
        self.land_use = v.Select(
            v_model  = [], 
            label    = ms.LAND_USE_SELECT_LABEL,
            items    = pm.land_use,
            multiple = True
        )
        
        # select the maximum allowable percent of tree cover
        self.subheader = v.Subheader(
            class_   = 'ml-0',
            children = [ms.MAX_ALLOW_TREECOVER_LABEL.format('')]
        )
        self.pcnt_treecover = v.Slider(
            v_model     = None,
            min         = 0,
            max         = 100, 
            thumb_label = True,
            disabled    = True
        )

        # create the tile 
        super().__init__(
            id_, 
            title, 
            inputs = [
                tile_txt, 
                self.land_use,
                self.subheader,
                self.pcnt_treecover
                
            ],
            **kwargs
        )
        
        # hide the border                           
        self.children[0].elevation = 0
        
        # link the widgets together 
        self.land_use.observe(self.__on_select, 'v_model')
        
    def __on_select(self, change):
        
        # create a readable str (can be done more efficiently I'm sure) 
        val = change['new']
        str_ = ''
        if len(val) == 1:
            str_ = val[0]
        elif len(val) > 1:
            str_  = ', '.join(val[:-1]) + ' & ' + val[-1]

        # change the title 
        self.subheader.children = [ms.MAX_ALLOW_TREECOVER_LABEL.format(str_)]
        
        # disabled the slider if nothing is set
        self.pcnt_treecover.disabled = (val == [])
            
                                     
                                     