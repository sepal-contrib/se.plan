import ipyvuetify as v 
from traitlets import observe, List, Unicode
from .. import parameter as pm
from ipywidgets import jslink
from sepal_ui import sepalwidgets as sw

class WeightSlider(v.Slider):
        
    _colors = {
        0: 'red',
        1: 'orange',
        2: 'yellow accent-3',
        3: 'light-green',
        4: 'green',
        5: 'primary',
        6: 'primary'
    }
    
    def __init__(self, name, default_value = 0, **kwargs):
        
        self.name = name
        
        super().__init__(
            max         = 6,
            min         = 0,
            track_color = 'grey',
            thumb_label = True,
            color       = self._colors[default_value],
            v_model     = default_value
        )
        
    @observe('v_model')
    def on_change(self, change):
        self.color = self._colors[change['new']]
        return 

#class WeightSlider(v.Row):
#    
#    _colors = {
#        0: 'red',
#        1: 'orange',
#        2: 'yellow accent-3',
#        3: 'light-green',
#        4: 'green',
#        5: 'primary',
#        6: 'primary'
#    }
#    
#    def __init__(self, name, default_value = 0, **kwargs):
#        
#        self.name = name
#        
#        self.minus = v.Icon(
#            color=self._colors[default_value],
#            class_='ml-5',
#            children=['mdi-minus']
#        )
#        
#        self.plus = v.Icon(
#            color=self._colors[default_value],
#            class_='mr-5',
#            children=['mdi-plus']
#        )
#        
#        self.text_field = v.TextField(
#            readonly = True,
#            full_width = False,
#            outlined = True,
#            background_color = self._colors[default_value],
#            v_model=None
#        ) 
#        
#        super().__init__(
#            Row=True,
#            xs12=True,
#            v_model = default_value,
#            children = [
#                self.minus,
#                self.text_field,
#                self.plus
#            ]
#        )
#        
#        # link all the variables       
#        jslink((self, 'v_model'), (self.text_field, 'v_model'))
#        self.minus.on_event('click', self.__on_minus)
#        self.plus.on_event('click', self.__on_plus)
#        
#            
#        
#    @observe('v_model')
#    def on_change(self, change):
#        
#        val = int(change['new'])
#        
#        # prevent value to exeed 6
#        if val < 0:
#            val = 0 
#            self.v_model = val
#        elif val > 6:
#            val = 6
#            self.v_model = val
#        
#        # change the color of the widget
#        self.minus.color = self._colors[val]
#        self.plus.color = self._colors[val]
#        self.text_field.background_color = self._colors[val]
#        
#        return 
#    
#    def __on_plus(self, event, data, widget):
#        
#        self.text_field.v_model += 1
#        
#        return 
#    
#    def __on_minus(self, event, data, widget):
#        
#        self.text_field.v_model -= 1
#        
#        return
    
class DefaultLayerTable(v.SimpleTable):
    
    _headers = [
        'Theme',
        'Sub theme',
        'Layer name',
        'Weight'
    ]
    
    def __init__(self):
        
        self.sliders = [WeightSlider(name) for name in pm.layer_list.layer_name]        
        
        # here we build a real table so "acrrocher vos ceintures"
        super().__init__(
            style_='{overflow: auto, max_height: 300px}',
            dense = True,
            children = [
                v.Html(tag = 'thead', children = [
                    v.Html(tag = 'tr', children = [
                        v.Html(tag = 'th', children = [h]) for h in self._headers
                    ])
                ]),
                v.Html(tag = 'tbody', children = [
                    v.Html(tag = 'tr', children = [
                        v.Html(tag = 'td', xs4=True, children = [row.theme]),
                        v.Html(tag = 'td', xs4=True, children = [row.subtheme]),
                        v.Html(tag = 'td', xs4=True, children = [row.layer_name]),
                        v.Html(tag = 'td', xs4=True, children = [self.sliders[i]]),
                    ]) for i, row in pm.layer_list.iterrows()
                ])
            ]
        )

class CustomLayerTable(v.SimpleTable):
    
    _headers = [
        'active',
        'Theme',
        'Sub theme',
        'Layer name',
        'Custom layer'
    ]
    
    def __init__(self):
        
        self.text_fields = [v.TextField(
            _metadata  = {'name' : row.layer_name},
            placeholder = row.gee_asset,
            v_model = None,
            disabled = True
        ) for i, row in pm.layer_list.iterrows()]   
        
        self.checkboxs = [v.Checkbox(
            _metadata = {'name': row.layer_name},
            v_model = False
        ) for i, row in pm.layer_list.iterrows()]
        
        # here we build a real table so "acrrocher vos ceintures"
        super().__init__(
            style_='{overflow: auto, max_height: 300px}',
            dense = True,
            children = [
                v.Html(tag = 'thead', children = [
                    v.Html(tag = 'tr', children = [
                        v.Html(tag = 'th', children = [h]) for h in self._headers
                    ])
                ]),
                v.Html(tag = 'tbody', children = [
                    v.Html(tag = 'tr', children = [
                        v.Html(tag = 'td', children = [self.checkboxs[i]]),
                        v.Html(tag = 'td', children = [row.theme]),
                        v.Html(tag = 'td', children = [row.subtheme]),
                        v.Html(tag = 'td', children = [row.layer_name]),
                        v.Html(tag = 'td', children = [self.text_fields[i]]),
                    ]) for i, row in pm.layer_list.iterrows()
                ])
            ]
        )
        
        # link the valu together
        self.__link_lines()
        
    def __link_lines(self):
        
        for checkbox in self.checkboxs:
            checkbox.observe(self.__on_check, 'v_model')
            
        return
        
        
    def __on_check(self, change):
        
        layer_name = change['owner']._metadata['name']
        
        for text_field in self.text_fields:
            if text_field._metadata['name'] == layer_name:
                text_field.disabled =  not change['new']
        
        return
    
    
class CustomizeLayerTile(sw.Tile):
    
    def __init__(self, **kwargs):
        
        # name the tile
        id_ = "manual_widget"
        title = "Manual layer selection"
        
        # create and assemble the two tables
        self.dlt = DefaultLayerTable()
        self.clt = CustomLayerTable()
        
        self.ep = v.ExpansionPanels(
            accordion = True,
            children = [
                v.ExpansionPanel(
                    key = 1,
                    children = [
                        v.ExpansionPanelHeader(children = ["Weighted default layers"]),
                        v.ExpansionPanelContent(children = [self.dlt])
                    ]
                ),
                v.ExpansionPanel(
                    key = 2,
                    children = [
                        v.ExpansionPanelHeader(children = ["Use customized layers"]),
                        v.ExpansionPanelContent(children = [self.clt])
                    ]
                )
            ]
        )
        
        # create the btns
        self.reset_to_questionnaire = sw.Btn(
            text   = 'Apply questionnaire answers', 
            icon   = 'mdi-help-center',
            class_ = 'mr-2'
        )
        self.reset_to_questionnaire.color = 'success'
        
        self.reset_to_default = sw.Btn(
            text   = 'Apply default parameters',
            icon   = 'mdi-restore', 
            class_ = 'ml-2'
        )
        self.reset_to_default.color = 'warning'
        
        self.btn_line = v.Row(
            class_   = 'mb-3',
            children = [self.reset_to_questionnaire, self.reset_to_default]
        )
        
        # create the txt 
        self.txt = sw.Markdown("On est des fous")
        
        # build the tile 
        super().__init__(
            id_, 
            title,
            inputs = [
                self.txt,
                self.btn_line,
                self.ep
            ],
            **kwargs
        )