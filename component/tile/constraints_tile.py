from traitlets import HasTraits, Unicode
import json

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component.message import cm
from component import parameter as cp
from component import widget as cw

class ConstraintTile(sw.Tile, HasTraits):
    
    # create custom_v_model as a traitlet
    # the traitlet List cannot be listened to so we're force to use Unicode json instead
    
    custom_v_model = Unicode('').tag(sync=True)
    
    def __init__(self):
        
        # name the tile 
        title = cm.constraints.title 
        id_= 'nested_widget'
        
        # write a quick explaination 
        tile_txt = sw.Markdown(cm.constraints.desc)
        
        # create the criteria list
        self.criterias = []
        for key, c in cp.criterias.items():
            
            header = c['header']
            value = c['content']
            
            if value == None: # binary criteria 
                crit = cw.Binary(key, header)
            elif isinstance(value, list): # dropdown values
                crit = cw.Dropdown(key, value, header)
            elif isinstance(value, int): # range values
                crit = cw.Range(key, value, header)
                
            self.criterias.append(crit)
            
        # create the each expansion-panel content 
        self.panels = v.ExpansionPanels(
            focusable=True,
            v_model=None, 
            hover=True,
            accordion=True,
            children=[cw.CustomPanel(k, self.criterias) for k in cp.criteria_types.keys()]
        )
           
        # default custom_v_model
        default_v_model = {c.name: c.custom_v_model for c in self.criterias}
        self.custom_v_model = json.dumps(default_v_model)
        
        # cration of the tile 
        super().__init__(id_, title, inputs = [tile_txt, self.panels])
        
        # hide the tile border
        self.children[0].elevation = 0
        
        # link the visibility of each criteria to the select widget
        [c.observe(self._on_change, 'custom_v_model') for c in self.criterias]
        self.panels.observe(self._on_panel_change, 'v_model')         
    
    def _on_change(self, change):
        
        # insert the new values in custom_v_model
        tmp = json.loads(self.custom_v_model)
        tmp[change['owner'].name] = change['new']
        self.custom_v_model = json.dumps(tmp)
        
        return
    
    def _on_panel_change(self, change):
        """revaluate each panel title when the v_model of the expansionpanels is changed"""
        
        # loop in the custom panels 
        for i, p in enumerate(self.panels.children):
            
            if i == change['new']:
                p.expand()
            else: 
                p.shrunk()
                
        return self
        
        
       