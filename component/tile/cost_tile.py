from sepal_ui import sepalwidgets as sw

from component.message import cm


class CostTile(sw.Tile):
    def __init__(self, aoi_view, layer_model):

        # get the models
        self.aoi_model = aoi_view.model
        self.layer_model = layer_model

        # name the tile
        title = cm.cost.title
        id_ = "nested_widget"

        super().__init__(id_, title)
