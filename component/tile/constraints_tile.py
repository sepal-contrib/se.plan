from traitlets import observe, HasTraits, Unicode, Integer
import json

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from .. import message as ms 
from .. import parameter as pm

class ConstraintTile(sw.Tile, HasTraits):
    
    # create custom_v_model as a traitlet
    # the traitlet List cannot be listened to so we're force to use Unicode json instead
    
    # build as such : 
    # { 'criteria_name' : [active (as bool), lt or gt (0-1), value], ...}
    custom_v_model = Unicode('').tag(sync=True)
    
    def __init__(self, **kwargs):
        
        # name the tile 
        title = "Constraints" 
        id_= 'nested_widget'
        
        # write a quick explaination 
        tile_txt = sw.Markdown(ms.CONSTRAINT_TXT)
        
        # select widget to select the actives criterias
        self.critera_select = v.Select(
            chips    = True,
            v_model  = None,
            items    = [*pm.criterias],
            label    = ms.CRITERIA_LABEL,
            multiple = True
        )
        
        # criteria widget that will be used to change the impact of each criteria and hide them
        self.criterias_values = []
        for key, value in pm.criterias.items():
            
            if value == None: # binary criteria 
                crit = Binary(key)
            elif isinstance(value, list):
                crit = Dropdown(key, value)
            elif isinstance(value, int):
                crit = Range(key, value)
                
            self.criterias_values.append(crit)
            
        default_v_model = {}
        for c in self.criterias_values:
            c.disable()
            default_v_model[c.name] = c.custom_v_model
            
        
        # default custom_v_model
        self.custom_v_model = json.dumps(default_v_model)
        
        # cration of the tile 
        super().__init__(
            id_, 
            title, 
            inputs = [tile_txt, self.critera_select] + self.criterias_values, 
            **kwargs
        )
        
        # hide the tile border
        self.children[0].elevation = 0
        
        # link the visibility of each criteria to the select widget
        self.critera_select.observe(self._on_select, 'v_model')
        for c in self.criterias_values:
            c.observe(self._on_change, 'custom_v_model')
        
    def _on_select(self, change):
            
        for criteria in self.criterias_values:
            # change the visibility and activation process
            if criteria.name in change['new']: 
                criteria.unable()
            else:
                criteria.disable()
        
        return         
    
    def _on_change(self, change):
        
        # insert the new values in custom_v_model
        tmp = json.loads(self.custom_v_model)
        tmp[change['owner'].name] = change['new']
        self.custom_v_model = json.dumps(tmp)
        
        return
        
        
       