from sepal_ui import sepalwidgets as sw

from .constraints_tile import ConstraintTile
from .potential_tile import PotentialTile
from .goal_tile import GoalTile
from .priority_tile import PriorityTile

from traitlets import observe, HasTraits, Unicode

import ipyvuetify as v
from ipywidgets import jslink


class QuestionaireIo():
    
    def __init__(self):
    
        self.constraints = ''
        self.potential = ''
        self.goals = ''
        self.priorities = ''

class QuestionnaireTile (sw.Tile):
    
    def __init__(self, io, **kwargs):
        
        # name the tile 
        title = "Questionnaire Identifying Restoration Objective & Goals"
        id_ = "questionnaire_widget"
        
        # build the tiles
        self.constraint_tile = ConstraintTile(),
        self.potential_tile  = PotentialTile(),
        self.goal_tile       = GoalTile(),
        self.priority_tile   = PriorityTile()
        
        self.tiles = [
            self.constraint_tile,
            self.potential_tile,
            self.goal_tile,
            self.priority_tile
        ]          
            
        # build the content and the stepper header
        step_content = []
        stepper_children = []
        for i, tile in enumerate(self.tiles):
            
            # for no reason the tiles are sometimes embed in a len 1 tuple
            tile = tile if type(tile) != tuple else tile[0]
            
            # build the stepper
            stepper_children.append(v.StepperStep(
                key      = i + 1,
                complete = False,
                step     = i + 1,
                editable = True,
                children = [tile.get_title()]
            ))
            stepper_children.append(v.Divider())
            
            # build the content 
            step_content.append(v.StepperContent(
                key      = i + 1,
                step     = i + 1, 
                children = [tile]
            ))
            
        stepper_children.pop()
        
        # build the stepper 
        stepper = v.Stepper(
            class_="mt-2",
             children=[
                 v.StepperHeader(children=stepper_children),
                 v.StepperItems(children=step_content)
             ]
        )
        
        # build the tile 
        super().__init__(id_, title, inputs=[stepper], **kwargs)
        
        #save the associated io and set the default value
        self.io = io
        self.io.constraints = self.constraint_tile[0].custom_v_model
        self.io.potential = self.potential_tile[0].custom_v_model
        self.io.goals = self.goal_tile[0].custom_v_model
        self.io.priorities = self.priority_tile.v_model
        
        
        # link the variable to the io 
        self.constraint_tile[0].observe(self.__on_constraint, 'custom_v_model')
        self.potential_tile[0].observe(self.__on_potential_tile, 'custom_v_model')
        self.goal_tile[0].observe(self.__on_goal_tile, 'custom_v_model')
        self.priority_tile.table.observe(self.__on_priority_tile, 'v_model')
        
    def __on_constraint(self, change):
        self.io.constraints = change['new']
        return
    
    def __on_potential_tile(self, change):
        self.io.potential = change['new']
        return
    
    def __on_goal_tile(self, change):
        self.io.goals = change['new']
        return
    
    def __on_priority_tile(self, change):
        self.io.priorities = change['new']
        return
        
        
        
        
        