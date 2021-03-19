from sepal_ui import sepalwidgets as sw

from component.message import cm

class DashThemeTile(sw.Tile):
    
    def __init__(self):
        
        txt = sw.Markdown(cm.dashboard.theme.txt)
        
        # create the tile 
        super().__init__(
            id_ = "dashboard_widget",
            title = cm.dashboard.theme.title,
            inputs = [txt]
        )
        
class DashRegionTile(sw.Tile):
    
    def __init__(self):
        
        super().__init__(
            id_ = 'dashboard_widget',
            title = cm.dashboard.region.title
        )