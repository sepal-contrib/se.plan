import ipyvuetify as v
from component.widget.buttons import CompareBtn, DrawMenuBtn, IconBtn, TextBtn
import sepal_ui.sepalwidgets as sw
from sepal_ui import color
from traitlets import Bool

from component import widget as cw
from component.message import cm
from component.model.recipe import Recipe
from component.widget.base_dialog import BaseDialog
from component.widget.map import SeplanMap


class MapToolbar(sw.Toolbar):
    aoi_tools = Bool(False).tag(sync=True)

    def __init__(self, recipe: Recipe, map_: SeplanMap, *args, **kwargs) -> None:

        self.height = "48px"
        super().__init__(*args, **kwargs)

        self.attributes = {"id": "map_toolbar"}
        self.recipe = recipe
        self.map_ = map_
        self.elevation = 0
        self.color = "accent"

        # Dialogs
        self.custom_aoi_dialog = cw.CustomAoiDialog(self.map_)
        self.import_aoi_dialog = cw.ImportAoiDialog(self.custom_aoi_dialog)
        self.download_map_dialog = cw.ExportMapDialog(self.recipe)
        self.compare_dialog = cw.CompareScenariosDialog(
            map_=self.map_, recipe=self.recipe
        )
        self.info_dialog = MapInfoDialog()

        # Main buttons
        self.btn_compute = TextBtn(cm.compute.btn)
        self.btn_compare = IconBtn(gliph="mdi-compare")
        self.btn_clean = IconBtn(gliph="mdi-broom")

        # Auxiliar buttons
        self.btn_draw = DrawMenu(
            gliph="mdi-draw",
            icon=True,
            small=True,
        )

        self.btn_download = IconBtn(
            gliph="fa-solid fa-circle-down",
        ).set_tooltip(cm.map.toolbar.tooltip.download, right=True, max_width="200px")

        self.btn_info = IconBtn(
            gliph="fa-solid fa-circle-info",
        ).set_tooltip(cm.map.toolbar.tooltip.info, right=True, max_width="200px")

        self.children = [
            # Main buttons
            self.btn_draw,
            # self.btn_load.with_tooltip,
            self.btn_download.with_tooltip,
            self.btn_info.with_tooltip,
            sw.Spacer(),
            self.btn_clean,
            self.btn_compare,
            sw.Divider(vertical=True, class_="mr-2"),
            self.btn_compute,
            # Auxiliar buttons
            # Dialogs - not visible on the toolbar
            self.custom_aoi_dialog,
            self.import_aoi_dialog,
            self.download_map_dialog,
            self.compare_dialog,
            self.info_dialog,
        ]

        self.btn_download.on_event(
            "click", lambda *_: self.download_map_dialog.open_dialog()
        )
        self.btn_info.on_event("click", lambda *_: self.info_dialog.open_dialog())
        self.btn_compare.on_event("click", lambda *_: self.compare_dialog.open_dialog())
        self.btn_clean.on_event("click", self.map_.clean_map)

        self.btn_draw.on_event("new", self.on_draw)
        self.btn_draw.on_event("show", self.on_draw)
        self.btn_draw.on_event("import", self.on_draw)

    def on_draw(self, widget, event, data):
        """Show or hide drawing control on the map."""

        if widget.attributes["id"] == "new":
            if not self.aoi_tools:
                widget.style_ = f"background-color: {color.menu};"
                self.map_.dc.show()
            else:
                widget.style_ = f"background-color: {color.main};"
                self.map_.dc.hide()

            self.aoi_tools = not self.aoi_tools

        elif widget.attributes["id"] == "import":
            self.map_.dc.hide()
            self.import_aoi_dialog.open_dialog()

        elif widget.attributes["id"] == "show":
            self.map_.dc.hide()
            self.custom_aoi_dialog.open_dialog(new_geom=False)


class DrawMenu(sw.Menu):
    def __init__(self, *args, **kwargs):
        self.offset_x = True
        self.v_model = False

        super().__init__(*args, **kwargs)

        btn_draw = DrawMenuBtn()

        self.v_slots = [
            {
                "name": "activator",
                "variable": "menuData",
                "children": btn_draw,
            }
        ]

        self.items = [
            v.ListItem(
                attributes={"id": title},
                children=[
                    v.ListItemTitle(children=[cm.map.toolbar.draw_menu[title]]),
                ],
            )
            for title in ["show", "import", "new"]
        ]

        self.children = [
            v.List(
                dense=True,
                children=self.items,
            ),
        ]

    def on_event(self, item_name, event):
        """Define an event based on the item name."""
        for item in self.items:
            if item.attributes["id"] == item_name:
                item.on_event("click", event)


class MapInfoDialog(BaseDialog):
    def __init__(self) -> None:
        super().__init__()

        self.well_read = False

        description = sw.Markdown("  \n".join(cm.map.txt))
        btn_close = TextBtn("Close", outlined=True)

        self.children = [
            v.Card(
                children=[
                    sw.CardTitle(children=[cm.map.title]),
                    sw.CardText(children=[description]),
                    sw.CardActions(children=[sw.Spacer(), btn_close]),
                ],
            ),
        ]

        btn_close.on_event("click", self.manual_close_dialog)

    def manual_close_dialog(self, *args):
        """Close the dialog and also update a trait so we can know that user already saw the info."""
        self.well_read = True
        self.close_dialog()
