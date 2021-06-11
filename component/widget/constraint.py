from traitlets import HasTraits, Integer, observe

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component.message import cm
from component import parameter as cp

class Constraint(sw.SepalWidget):
    
    custom_v_model = Integer().tag(sync=True)
    
    def __init__(self, name = 'name', header='header', id_='id', **kwargs):
        
        self.id = id_
        self.header = header
        self.name = name
        self.custom_v_model = -1
        self.persistent_hint=True
        self.class_ = 'ma-5'
        
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
        self.hide()
        
        return self 
    
    def unable(self):
        
        # update the custom v_model
        self.custom_v_model = self.v_model
        
        # show the component 
        self.show()
        
        return self

class Binary(v.Switch, Constraint):
    
    def __init__(self, name, header, **kwargs):
        
        super().__init__(
            disabled = True,
            name = name,
            header=header,
            label = name,
            v_model = True,
            **kwargs
        )
        
class Dropdown(v.Select, Constraint):
    
    def __init__(self, name, items, header, **kwargs):
        
        super().__init__(
            name = name,
            label = name,
            header = header,
            items = items,
            v_model = int(items[0]['value']),
            **kwargs
        )
        
        
class Range(v.Slider, Constraint):
    
    def __init__(self, name, max, header, **kwargs):
        
        super().__init__(
            persistent_hint = True,
            hint = cm.questionnaire.slider_hint,
            name = name, 
            header = header,
            label = name,
            max = max,
            v_model = 0,
            thumb_label=True,
            **kwargs
        )
        
class CustomPanel(v.ExpansionPanel, sw.SepalWidget):
    
    def __init__(self, category, criterias):
        
        # save title name 
        self.title = category
        
        # create a header, as nothing is selected by defaul it should only display the title
        self.header = v.ExpansionPanelHeader(children=[cp.criteria_types[category]])
        
        # link the criterias to the select 
        self.criterias = [c.disable() for c in criterias if c.header == category] 
        self.select = v.Select(
            class_ = 'mt-5',
            small_chips = True,
            v_model = None,
            items = [c.name for c in self.criterias],
            label = cm.constraints.criteria_lbl,
            multiple = True,
            deletable_chips = True
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
        