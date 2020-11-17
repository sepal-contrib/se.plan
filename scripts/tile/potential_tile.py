from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
from .. import message as ms
from .. import parameter as pm
import json
from traitlets import HasTraits, Unicode

class PotentialTile(sw.Tile, HasTraits):
    
    # create custom_v_model as a traitlet
    # the traitlet List cannot be listened to so we were force to use Unicode json instead
    custom_v_model = Unicode('').tag(sync=True)
    
    def __init__(self, **kwargs):
        
        # name the tile 
        title = "Restoration potential and land use" 
        id_ = 'nested_widget'
        
        #default custom_v_model 
        self.custom_v_model = json.dumps([[],0])
        
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
        self.pcnt_treecover.observe(self.__on_change_treecover, 'v_model')
        
    def __on_select(self, change):
        
        val = change['new']
        
        #change the custom_v_model
        tmp = json.loads(self.custom_v_model)
        tmp[0] = val
        self.custom_v_model = json.dumps(tmp)
        
        # create a readable str (can be done more efficiently I'm sure) 
        str_ = ''
        if len(val) == 1:
            str_ = val[0]
        elif len(val) > 1:
            str_  = ', '.join(val[:-1]) + ' & ' + val[-1]

        # change the title 
        self.subheader.children = [ms.MAX_ALLOW_TREECOVER_LABEL.format(str_)]
        
        # disabled the slider if nothing is set
        self.pcnt_treecover.disabled = (val == [])
        
        return 
            
    def __on_change_treecover(self, change):
        
        #change the custom_v_model
        tmp = json.loads(self.custom_v_model)
        tmp[1] = change['new']
        self.custom_v_model = json.dumps(tmp)
        
        return
                                     