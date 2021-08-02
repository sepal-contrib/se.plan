from traitlets import HasTraits, Any, observe, dlink

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
import ee

from component.message import cm
from component import parameter as cp

ee.Initialize()

class Constraint(sw.SepalWidget, v.Row):
    
    custom_v_model = Any(-1).tag(sync=True)
    
    def __init__(self, widget, name = 'name', header='header', id_='id', **kwargs):
        
        # default
        self.id = id_
        self.header = header
        self.name = name
        self.class_ = 'ma-5'
        self.widget = widget
        self.align_center = True
        
        # creat a pencil btn 
        self.btn = v.Icon(children=['mdi-pencil'], _metadata={'layer': id_})
        
        # create the row 
        super().__init__(**kwargs)
        
        self.children = [
            v.Flex(align_center=True, xs1=True, children=[self.btn]),
            v.Flex(align_center=True, xs11=True, children=[self.widget])
        ]
        
        # link widget and custom_v_model
        dlink((self.widget, 'v_model'), (self, 'custom_v_model'))
        
    @observe('v_model')
    def _on_change(self, change):
        
        # update the custom v_model
        self.custom_v_model = change['new']
        
        return
    
    def disable(self):
        
        # update the custom v_model 
        self.custom_v_model = -1
        
        # hide the component 
        self.hide()
        
        return self 
    
    def unable(self):
        
        # update the custom v_model
        self.custom_v_model = self.widget.v_model
        
        # show the component 
        self.show()
        
        return self

class Binary(Constraint):
    
    def __init__(self, name, header, id_, **kwargs):
        
        widget = v.Switch(
            readonly = True,
            persistent_hint=True,
            v_model=True,
            label = name,
            **kwargs
        )
        
        super().__init__(widget, name=name, header=header, id_=id_)
        
class Dropdown(Constraint):
    
    def __init__(self, name, items, header, **kwargs):
        
        widget = v.Select(
            label = name,
            persistent_hint=True,
            items = items,
            v_model = int(items[0]['value']),
            **kwargs
            
        )
        
        super().__init__(widget, name=name, header=header)
        
        
class Range(Constraint):
    
    LABEL = ['low', 'medium', 'hight']
    
    def __init__(self, name, header, id_, **kwargs):
        
        widget = v.Slider(
            label = name,
            max = 1,
            step = .1,
            v_model = 0,
            thumb_label=True,
            **kwargs
        )
        
        super().__init__(widget, name = name, header = header, id_=id_)
        
        
    def set_values(self, geometry, layer):
        
        print(self.name)
        
        # compute the min and the max for the specific geometry and layer
        ee_image = ee.Image(layer)
        
        # get min 
        min_ = ee_image.reduceRegion(
            reducer = ee.Reducer.min(),
            geometry = geometry,
            scale = 250
        )
        min_ = list(min_.getInfo().values())[0]
        print(min_)
        
        # get max 
        max_ = ee_image.reduceRegion(
            reducer = ee.Reducer.max(),
            geometry = geometry,
            scale = 250
        )
        max_ = list(max_.getInfo().values())[0]
        print(max_)
        
        self.widget.min = round(min_, 2)
        self.widget.max = round(max_, 2)
        
        # set the number of steps by stting the step parameter (100)
        self.widget.step = round((self.widget.max-self.widget.min)/100, 2)
        
        # display ticks label with low medium and high values            
        self.widget.tick_labels = [self.LABEL[i//25 - 1] if i%25 == 0 and not (i in [0,100]) else '' for i in range(101)]
        
        return self
    
class CustomPanel(v.ExpansionPanel, sw.SepalWidget):
    
    def __init__(self, category, criterias):
        
        # save title name 
        self.title = category
        
        # create a header, as nothing is selected by defaul it should only display the title
        self.header = v.ExpansionPanelHeader(children=[cp.criteria_types[category]])
        
        # link the criterias to the select 
        self.criterias = [c.disable() for c in criterias if c.header == category] 
        self.select = v.Select(
            disabled=True, # disabled until the aoi is selected
            class_ = 'mt-5',
            small_chips = True,
            v_model = None,
            items = [c.name for c in self.criterias],
            label = cm.constraints.criteria_lbl,
            multiple = True,
            deletable_chips = True,
            persistent_hint = True,
            hint = "select an AOI first"
        )
            
        # create the content, nothing is selected by default so Select should be empty and criterias hidden 
        criteria_flex = [v.Flex(xs12=True, children=[c]) for c in self.criterias]
        self.content = v.ExpansionPanelContent(children=[v.Layout(row=True, children=[self.select]+criteria_flex)])
        
        # create the actual panel
        super().__init__(children=[self.header, self.content])
        
        # link the js behaviour
        self.select.observe(self._show_crit, 'v_model')
        
    def _show_crit(self, change):
        
        for c in self.criterias:
            if c.name in change['new']:
                c.unable()
            else:
                c.disable()
        
        return self
        
    def expand(self):
        """when the custom panel expand I want to display only the title"""
        
        self.header.children = [cp.criteria_types[self.title]]
        
        return self
    
    def shrunk(self):
        """ when shrunked I want to display the chips int the header along the title"""
        
        # get the title 
        title = cp.criteria_types[self.title]
        
        # get the chips
        chips = v.Flex(children=[v.Chip(class_='ml-1 mr-1', small=True, children=[c.name]) for c in self.criterias if c.viz])

        # write the new header content 
        self.header.children = [title, chips]
        
        return self
        