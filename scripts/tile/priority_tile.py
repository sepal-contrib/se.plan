import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from traitlets import Unicode, HasTraits
from .. import parameter as pm 
from .. import message as ms
import json
from ipywidgets import jslink

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
#_labels = [
#        'no importance',
#        'low importance',
#        'neutral',
#        'important',
#        'very important',
#    ]
#        
#    _colors = [
#        'red',
#        'orange',
#        'yellow accent-3',
#        'light-green',
#        'green'
#    ]    
    
class CustomCheckbox(v.Checkbox):
    
    def __init__(self, color, val, label, default = False):
        
        super().__init__(
            color = color,
            _metadata = {'label': label, 'val': val},
            v_model = default,
        )
        
class PriorityTable(v.SimpleTable):
    
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
    
    _DEFAULT_V_MODEL = {name: 0 for name in pm.priorities}
    
    def __init__(self):
        
        
        # construct the checkbox list
        self.checkbox_list = {}
        for name in pm.priorities:
            line = []
            for i, color in enumerate(self._colors):
                line.append(CustomCheckbox(color, i, name, i==0))
            self.checkbox_list[name] = line
            
        # construct the rows of the table
        rows = []
        for name in pm.priorities:
            row  = [v.Html(tag = 'td', children = [name])]
            for j in range(len(self._colors)):
                row.append(v.Html(tag = 'td', children = [self.checkbox_list[name][j]]))
            rows.append(v.Html(tag = 'tr', children = row))
        
        # create the table
        super().__init__(
            v_model = json.dumps(self._DEFAULT_V_MODEL),
            children = [
                v.Html(tag = 'thead', children = [
                    v.Html(tag = 'tr', children = (
                        [ v.Html(tag = 'th', children = ['priority'])]
                        + [v.Html(tag = 'th', children = [label]) for label in self._labels]
                    ))
                ]),
                v.Html(tag = 'tbody', children = rows)
            ]
        )
        
        # link the checks with the v_model
        for name in pm.priorities:
            for check in self.checkbox_list[name]:
                check.observe(self._on_check_change, 'v_model')
        
    def _on_check_change(self, change):
        
        line = change['owner']._metadata['label']
        
        # if checkbox is unique and chang == false recheck 
        if change['new'] == False:
            unique = True
            for check in self.checkbox_list[line]:
                if check.v_model == True:
                    unique = False 
                    break
            
            change['owner'].v_model = unique
        
        else:
            # uncheck all the others in the line
            for check in self.checkbox_list[line]:
                if check != change['owner']:
                    check.v_model = False
            
            # change the table model 
            tmp = json.loads(self.v_model)
            tmp[line] = change['owner']._metadata['val']
            self.v_model = json.dumps(tmp)
            
        return
            
        
            
class PriorityTile (sw.Tile, HasTraits):
    
    custom_v_model = Unicode().tag(sync=True)
    
    def __init__(self, **kwargs):
        
        # name the tile
        title = "Restoration priorities"
        id_ = "nested_widget"
        
        # create the sliders
        self.table = PriorityTable()
        
        # build the tile
        super().__init__(
            id_, 
            title, 
            inputs = [self.table],
            **kwargs
        )
        
        self.v_model = json.dumps(self.table._DEFAULT_V_MODEL)
        
        # hide the borders 
        self.children[0].elevation = 0
        
        #link the widgets to the tile 
        jslink((self, 'v_model'),(self.table, 'v_model'))
        
        
        
        
        
        
        
        