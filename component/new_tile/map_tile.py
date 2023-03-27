from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from sepal_ui import aoi
from ipywidgets import HTML
from IPython.display import display

from component import new_model as cmod
from component import new_widget as cw

from .export_control import ExportControl
from .about_control import AboutControl
from .aoi_control import AoiControl
from .priority_control import PriorityControl
from .cost_control import CostControl


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = sm.SepalMap()
        self.map.add_basemap("SATELLITE")

        # replace the basemapcontrol
        self.map.remove_control(
            next(c for c in self.map.controls if isinstance(c, sm.LayersControl))
        )
        self.map.add_control(cw.LayersControl(self.map))

        # add a layerstate (there are too many of them)
        layer_state_control = sm.LayerStateControl(self.map, position="bottomleft")

        # create the models
        aoi_model = aoi.AoiModel()
        priority_model = cmod.PriorityModel()
        cost_model = cmod.CostModel()

        # create the parameters controls
        full_control = sm.FullScreenControl(self.map, True, True, position="topright")
        val_control = sm.InspectorControl(self.map, False, position="bottomleft")
        export_control = ExportControl(position="bottomleft")
        about_control = AboutControl(position="bottomleft")
        aoi_control = AoiControl(self.map, aoi_model, position="bottomright")
        priority_control = PriorityControl(
            self.map, priority_model, position="bottomright"
        )
        cost_control = CostControl(self.map, cost_model, position="bottomright")

        # create the viz controls
        priority_layer_control = cw.PriorityLayersControl(
            self.map, aoi_model, priority_model, position="topleft"
        )
        cost_layer_control = cw.CostLayersControl(
            self.map, aoi_model, cost_model, position="topleft"
        )

        # add them on the map
        self.map.add(full_control)
        self.map.add_control(layer_state_control)
        self.map.add(val_control)
        self.map.add(export_control)
        self.map.add(about_control)
        self.map.add(cost_control)
        self.map.add(priority_control)
        self.map.add(aoi_control)
        self.map.add(priority_layer_control)
        self.map.add(cost_layer_control)

        super().__init__(id_="map_tile", title="", inputs=[self.map])
