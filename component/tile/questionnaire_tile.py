from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component.message import cm
from .constraints_tile import ConstraintTile
from .priority_tile import PriorityTile

class QuestionnaireTile (sw.Tile):
    
    def __init__(self, io, **kwargs):
        
        # name the tile 
        title = cm.questionnaire.title
        id_ = "questionnaire_widget"
        
        # build the tiles
        self.constraint_tile = ConstraintTile()
        self.priority_tile   = PriorityTile()
        
        self.tiles = [
            self.constraint_tile,
            self.priority_tile
        ]          
            
        # build the content and the stepper header
        tab_content = []
        for i, tile in enumerate(self.tiles):
            
            # add the title and content 
            tab_content.append(v.Tab(children=[tile.get_title()]))
            tab_content.append(v.TabItem(children=[tile]))
        
        # build the tabs 
        tabs = tabs = v.Tabs(
            class_='mt-5',
            fixed_tabs = True,
            centered = True,
            children = tab_content
        )
        
        # build the tile 
        super().__init__(id_, title, inputs=[tabs], **kwargs)
        
        # save the associated io and set the default value
        self.io = io
        self.io.constraints = self.constraint_tile.custom_v_model
        self.io.priorities = self.priority_tile.v_model
        
        
        # link the variable to the io 
        self.constraint_tile.observe(self.__on_constraint, 'custom_v_model')
        self.priority_tile.table.observe(self.__on_priority_tile, 'v_model')
        
    def __on_constraint(self, change):
        self.io.constraints = change['new']
        return
    
    def __on_priority_tile(self, change):
        self.io.priorities = change['new']
        return
        
        
        
        
        