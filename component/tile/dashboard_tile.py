from sepal_ui import sepalwidgets as sw

from component.message import cm

class DashboardTile(sw.Tile):
    
    def __init__(self):
        
        
        # create the tile 
        super().__init__(
            id_ = "dashboard_widget",
            title = cm.dashboard.title
        )