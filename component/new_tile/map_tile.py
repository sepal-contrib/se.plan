from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from sepal_ui import aoi
from ipywidgets import HTML
from IPython.display import display

from component import new_model as cmod

from .export_control import ExportControl
from .about_control import AboutControl
from .aoi_control import AoiControl
from .priority_control import PriorityControl


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = sm.SepalMap()
        self.map.add_basemap("SATELLITE")

        # create the models
        aoi_model = aoi.AoiModel()
        priority_model = cmod.PriorityModel()

        # create the controls
        full_control = sm.FullScreenControl(self.map, True, True, position="topright")
        val_control = sm.InspectorControl(self.map, False, position="bottomleft")
        export_control = ExportControl(position="bottomleft")
        about_control = AboutControl(position="bottomleft")
        aoi_control = AoiControl(self.map, aoi_model, position="bottomright")
        priority_control = PriorityControl(
            self.map, priority_model, position="bottomright"
        )

        # add them on the map
        self.map.add(full_control)
        self.map.add(val_control)
        self.map.add(export_control)
        self.map.add(about_control)
        self.map.add(priority_control)
        self.map.add(aoi_control)

        super().__init__(id_="map_tile", title="", inputs=[self.map])
