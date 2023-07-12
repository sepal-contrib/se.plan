import sepal_ui.scripts.decorator as sd
import sepal_ui.sepalwidgets as sw
from traitlets import Bool

from component import widget as cw
from component.message import cm
from component.scripts.seplan import Seplan
from component.widget.map import SeplanMap


class MapBar(sw.Toolbar):
    aoi_tools = Bool(False).tag(sync=True)

    def __init__(self, model: Seplan, map_: SeplanMap, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.attributes = {"id": "map_toolbar"}
        self.model = model
        self.map_ = map_

        # Dialogs
        self.save_geom_dialog = cw.CustomAoiDialog(self.map_)
        self.download_map_dialog = cw.ExportMapDialog()
        self.load_shape_dialog = cw.LoadDialog()

        # Main buttons
        self.btn_create_map = sw.Btn(cm.compute.btn, class_="ma-2")
        self.btn_dashboard = sw.Btn(
            cm.map.compute_dashboard, class_="ma-2", disabled=True
        )
        # Auxiliar buttons
        self.btn_draw = sw.Btn(
            gliph="mdi-draw",
            icon=True,
            color="primary",
        ).set_tooltip(cm.map.toolbar.tooltip.draw, right=True, max_width="200px")

        self.btn_download = sw.Btn(
            gliph="mdi-download",
            icon=True,
            color="primary",
        ).set_tooltip(cm.map.toolbar.tooltip.download, right=True, max_width="200px")

        self.btn_load = sw.Btn(
            gliph="mdi-upload",
            icon=True,
            color="primary",
        ).set_tooltip(cm.map.toolbar.tooltip.load, right=True, max_width="200px")

        self.children = [
            # Main buttons
            self.btn_draw.with_tooltip,
            self.btn_load.with_tooltip,
            self.btn_download.with_tooltip,
            sw.Spacer(),
            sw.Divider(vertical=True, class_="mr-2"),
            self.btn_create_map,
            self.btn_dashboard,
            # Auxiliar buttons
            # Dialogs - not visible on the toolbar
            self.save_geom_dialog,
            self.download_map_dialog,
            self.load_shape_dialog,
        ]

        # self.load_shape_dialog.btn.on_event("click", self._load_shapes)

        self.btn_download.on_event(
            "click", lambda *_: self.download_map_dialog.open_dialog()
        )

        self.btn_load.on_event("click", lambda *_: self.load_shape_dialog.open_dialog())
        self.btn_draw.on_event("click", self.on_draw)

    def on_draw(self, *_):
        """Show or hide drawing control on the map."""
        self.map_.dc.show() if not self.aoi_tools else self.map_.dc.hide()
        self.aoi_tools = not self.aoi_tools

    @sd.switch("loading", on_widgets=["dialog"])
    def open_new_dialog(self, *args) -> None:
        """open the new benefit dialog."""
        self.dialog.open_new()
