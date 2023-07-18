import ipyvuetify as v
import sepal_ui.sepalwidgets as sw
from sepal_ui import color
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
        self.load_shape_dialog = cw.LoadDialog(self.map_)

        # Main buttons
        self.btn_create_map = sw.Btn(cm.compute.btn, class_="ma-2")
        self.btn_dashboard = sw.Btn(
            cm.map.compute_dashboard, class_="ma-2", disabled=True
        )
        # Auxiliar buttons
        self.btn_draw = DrawMenu(
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

        self.btn_download.on_event(
            "click", lambda *_: self.download_map_dialog.open_dialog()
        )

        self.btn_load.on_event("click", lambda *_: self.load_shape_dialog.open_dialog())

        self.btn_draw.on_event("new", self.on_draw)
        self.btn_draw.on_event("show", self.on_draw)

    def on_draw(self, widget, event, data):
        """Show or hide drawing control on the map."""
        if widget.attributes["id"] == "new":
            if not self.aoi_tools:
                print(widget)
                widget.style_ = f"background-color: {color.menu};"
                self.map_.dc.show()
            else:
                widget.style_ = f"background-color: {color.main};"
                self.map_.dc.hide()

            self.aoi_tools = not self.aoi_tools

        elif widget.attributes["id"] == "show":
            self.save_geom_dialog.open_dialog(new_geom=False)


class DrawMenu(sw.Menu):
    def __init__(self, *args, **kwargs):
        self.offset_x = True
        self.v_model = (False,)

        super().__init__(*args, **kwargs)

        btn_draw = v.Btn(
            v_on="menuData.on",
            # small=True,
            children=[
                v.Icon(children=["mdi-draw"], small=True),
                v.Icon(children=["fa fa-caret-down"], small=True, right=True),
            ],
        )

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
                style_=f"background-color: {color.main};",
                children=[
                    v.ListItemTitle(children=[cm.map.toolbar.draw_menu[title]]),
                ],
            )
            for title in ["new", "show"]
        ]

        self.children = [
            v.List(
                style_=f"background-color: {color.main};",
                dense=True,
                children=self.items,
            ),
        ]

    def on_event(self, item_name, event):
        """Define an event based on the item name."""
        for item in self.items:
            if item.attributes["id"] == item_name:
                item.on_event("click", event)
