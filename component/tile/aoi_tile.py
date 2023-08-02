import sepal_ui.sepalwidgets as sw
from ipyleaflet import WidgetControl
from sepal_ui.aoi.aoi_view import AoiView
from sepal_ui.mapping import SepalMap

from component.model.recipe import Recipe


class AoiTile(sw.Layout):
    """Custo AOI Tile."""

    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.class_ = "d-block"
        self._metadata = {"mount_id": "aoi_tile"}

        super().__init__()

        self.map_ = SepalMap(gee=True)
        self.map_.dc.hide()
        self.map_.layout.height = "750px"
        self.map_.min_zoom = 2

        # Build the aoi view with our custom aoi_model
        self.view = AoiView(
            model=self.recipe.seplan_aoi.aoi_model,
            map_=self.map_,
            methods=["-POINTS"],
        )

        aoi_control = WidgetControl(
            widget=self.view, position="topleft", transparent_bg=True
        )

        self.map_.add(aoi_control)
        self.children = [self.map_]
