from traitlets import observe

import ipyvuetify as v

from component import parameter as cp

class WeightSlider(v.Slider):
    
    def __init__(self, name, default_value = 0, **kwargs):
        
        self.name = name
        
        super().__init__(
            max         = 10,
            min         = 0,
            track_color = 'grey',
            thumb_label = 'always',
            color       = cp.gradient(11)[default_value],
            v_model     = default_value,
            class_      = 'ml-5 mr-5'
        )
        
    @observe('v_model')
    def on_change(self, change):
        self.color = cp.gradient(11)[change['new']]
        return 