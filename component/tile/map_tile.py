from sepal_ui import sepalwidgets as sw 
from sepal_ui import mapping as sm

from component.message import cm

class MapTile(sw.Tile):
    
    def __init__(self):
        
        # create the map 
        self.m = sm.SepalMap()
        
        # create the tile
        super().__init__(
            id_ = "map_widget",
            title = cm.map.title,
            inputs = [self.m]
        )