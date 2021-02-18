from traitlets import HasTraits, Integer, observe

from sepal_ui.scripts import utils as su
import ipyvuetify as v


class Constraint(HasTraits):
    
    custom_v_model = Integer().tag(sync=True)
    
    def __init__(self, name = 'name', **kwargs):
        
        self.name = name
        self.custom_v_model = -1
        
        super().__init__(**kwargs)
        
    @observe('v_model')
    def _on_change(self, change):
        
        # update the custom v_model
        self.custom_v_model = change['new']
        
        return
    
    def disable(self):
        
        # update the custom v_model 
        self.custom_v_model = -1
        
        # hide the component 
        su.hide_component(self)
        
        return 
    
    def unable(self):
        
        # update the custom v_model
        self.custom_v_model = self.v_model
        
        # hide the component 
        su.show_component(self)
        
        return 

class Binary(v.Switch, Constraint):
    
    def __init__(self, name, **kwargs):
        
        super().__init__(
            name = name,
            label = name,
            v_model = False
        )
        
class Dropdown(v.Select, Constraint):
    
    def __init__(self, name, items, **kwargs):
        
        super().__init__(
            name = name,
            label = name,
            items = items,
            v_model = 10
        )
        
        
class Range(v.Slider, Constraint):
    
    def __init__(self, name, max, **kwargs):
        
        super().__init__(
            name = name, 
            label = name,
            max = max,
            v_model = 0,
            thumb_label=True
        )