import ipyvuetify as v
from component.frontend.icons import icon
from component.widget.buttons import DrawMenuBtn, IconBtn, TextBtn
from component.widget.custom_widgets import MapInfoDialog
import sepal_ui.sepalwidgets as sw
from sepal_ui.sepalwidgets.btn import TaskButton

from traitlets import Bool

from component import widget as cw
from component.message import cm
from sepal_ui.scripts.gee_interface import GEEInterface
from component.model.recipe import Recipe
from component.widget.base_dialog import BaseDialog
from component.widget.map import SeplanMap
from component.widget.alert_state import Alert


class MapToolbar(sw.Toolbar):
    aoi_tools = Bool(False).tag(sync=True)

    def __init__(
        self,
        recipe: Recipe,
        map_: SeplanMap,
        alert: Alert,
        sepal_session=None,
        gee_interface: GEEInterface = None,
        *args,
        **kwargs,
    ) -> None:

        self.height = "48px"
        super().__init__(*args, **kwargs)

        self.gee_interface = gee_interface
        self.attributes = {"id": "map_toolbar"}
        self.recipe = recipe
        self.map_ = map_
        self.elevation = 0
        self.color = "accent"

        # Dialogs
        self.custom_aoi_dialog = cw.CustomAoiDialog(self.map_)
        self.import_aoi_dialog = cw.ImportAoiDialog(
            self.custom_aoi_dialog, gee_interface=self.gee_interface
        )
        self.compare_dialog = cw.CompareScenariosDialog(
            type_="map",
            map_=self.map_,
            main_recipe=self.recipe,
            alert=alert,
            sepal_session=sepal_session,
            gee_interface=gee_interface,
        )
        self.info_dialog = MapInfoDialog()

        # Main buttons - removed btn_compute and download_map_dialog (moved to right panel)

        # Auxiliar buttons - removed btn_download (moved to right panel)
        self.btn_info = IconBtn(
            gliph="fa-solid fa-circle-info",
        ).set_tooltip(cm.map.toolbar.tooltip.info, right=True, max_width="200px")

        self.btn_compare = IconBtn(gliph=icon("compare")).set_tooltip(
            cm.map.toolbar.tooltip.compare, right=True, max_width="200px"
        )
        self.btn_clean = IconBtn(gliph=icon("broom")).set_tooltip(
            cm.map.toolbar.tooltip.clean, right=True, max_width="200px"
        )

        self.children = [
            # Main buttons - btn_compute and btn_download moved to right panel
            self.btn_info.with_tooltip,
            sw.Spacer(),
            self.btn_clean.with_tooltip,
            self.btn_compare.with_tooltip,
            # Dialogs - not visible on the toolbar (removed download_map_dialog)
            self.custom_aoi_dialog,
            self.import_aoi_dialog,
            self.compare_dialog,
            self.info_dialog,
        ]

        # Event handlers - removed btn_download handler (moved to right panel)
        self.btn_info.on_event("click", lambda *_: self.info_dialog.open_dialog())
        self.btn_compare.on_event("click", lambda *_: self.compare_dialog.open_dialog())
        self.btn_clean.on_event("click", self.map_.clean_map)
