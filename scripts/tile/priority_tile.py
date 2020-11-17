import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from traitlets import Unicode, HasTraits
from .. import parameter as pm 
from .. import message as ms
import json

class satisfactionSlider(v.Row, HasTraits):
    
    # create custom_v_model as a traitlet
    custom_v_model = Unicode('').tag(sync=True)
    
    _labels = [
        'no importance',
        'low importance',
        'neutral',
        'important',
        'very important',
    ]
        
    _colors = [
        'red',
        'orange',
        'yellow accent-3',
        'light-green',
        'green'
    ]
    
    def __init__(self, label, default_value = 2, **kwargs):
        
        self.name = label
        
        # build the slider
        self.subheader = v.Subheader(children=[label])
        self.slider = v.Slider(
            max             = 4,
            min             = 0,
            track_color     = 'grey',
            tick_size       = 4,
            ticks           = True,
            label            = self._labels[default_value],
            color           = self._colors[default_value],
            v_model         = default_value
        )
        
        # build the row 
        super().__init__(
            children = [
                v.Flex(xs12 = True, children = [self.subheader]),
                v.Flex(xs12 = True, children = [self.slider])
            ],
            **kwargs
        )
        
        # default values of the v_model 
        self.custom_v_model = json.dumps([label, default_value])
        
        #link the widgets together
        self.slider.observe(self.on_change, 'v_model')
        
    def on_change(self, change):
        self.slider.color = self._colors[change['new']]
        self.slider.label = self._labels[change['new']]
        
        tmp = json.loads(self.custom_v_model)
        tmp[1] = change['new']
        self.custom_v_model = json.dumps(tmp)
        
        return
        
        
class PriorityTile (sw.Tile, HasTraits):
    
    # create custom_v_model as a traitlet
    custom_v_model = Unicode('').tag(sync=True)
    
    def __init__(self, **kwargs):
        
        # name the tile
        title = "Restoration priorities"
        id_ = "nested_widget"
        
        # create the sliders
        self.satisfation_silders = [satisfactionSlider(name) for name in pm.priorities]
        
        # build the tile
        super().__init__(
            id_, 
            title, 
            inputs = self.satisfation_silders,
            **kwargs
        )
        
        #default value for the priorities
        self.custom_v_model = json.dumps({name: 2 for name in pm.priorities})
        
        # hide the borders 
        self.children[0].elevation = 0
        
        #link the widgets to the tile 
        self.__link_satisfaction_slider()
    
    def __link_satisfaction_slider(self):
        
        for slider in self.satisfation_silders:
            slider.observe(self.__on_change, 'custom_v_model')
            
        return 
    
    def __on_change(self, change):
        
        val = json.loads(change['new'])
        
        tmp = json.loads(self.custom_v_model)
        tmp[val[0]] = val[1]
        self.custom_v_model = json.dumps(tmp)
        
        return
        
        
        
        
        
        
        
        