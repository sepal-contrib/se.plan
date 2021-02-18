from traitlets import HasTraits, Unicode

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component.message import cm
from component import parameter as cp


class GoalTile(sw.Tile, HasTraits):
    
    # create custom_v_model as a traitlet
    custom_v_model = Unicode('').tag(sync=True)
    
    def __init__(self, **kwargs):
        
        # name the tile
        title = "Restoration goals"
        id_ = "nested_widget"
        
        #default value 
        custom_v_model = None
        
        # select the goals
        self.select_goal = v.Select(
            label   = cm.questionnaire.goal_lbl,
            items   = cp.goals,
            v_model = None
        )
        
        # create the tile 
        super().__init__(
            id_, 
            title, 
            inputs = [self.select_goal],
            **kwargs
        )
        # hide the borders
        self.children[0].elevation = 0
        
        #link the widget to the tile
        self.select_goal.observe(self.__on_change, 'v_model')
        
    def __on_change(self, change):
        self.custom_v_model = change['new']
        