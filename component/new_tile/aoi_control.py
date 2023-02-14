from sepal_ui import aoi
from sepal_ui import color as sc
from sepal_ui import mapping as sm

from component.message import cm


class AoiControl(sm.MenuControl):
    def __init__(self, map_, **kwargs):

        # create the view
        style = {
            "stroke": True,
            "color": sc.primary,
            "weight": 2,
            "opacity": 1,
            "fill": False,
        }
        self.view = aoi.AoiView(map_=map_, map_style=style)
        self.view.elevation = False
        self.view.btn.color = "secondary"
        self.view.class_list.add("ma-5")

        # create the control
        super().__init__(
            "fa-solid fa-map-marker-alt",
            self.view,
            m=map_,
            card_title=cm.aoi_control.title,
            **kwargs
        )
