"""Single entry-point dialog that consolidates all custom-geometry actions.

Replaces the right-panel button stack with one "Custom geometries" button
that opens a modal exposing Admin sub-area / Draw / Import as a compact
list, alongside the table of existing custom geometries. Each list item
dispatches via ``SeplanMap.on_draw`` (which closes this dialog before
launching the chosen flow).
"""

import ipyvuetify as v
import sepal_ui.sepalwidgets as sw

import component.parameter as cp
from component.frontend.icons import icon
from component.message import cm
from component.widget import custom_widgets as cw
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn


class CustomGeometriesDialog(BaseDialog):
    """Modal hub for managing custom sub-AOIs."""

    def __init__(self, map_):
        super().__init__()
        self.attributes = {"id": "custom_geometries_dialog"}
        self.map_ = map_

        title = sw.CardTitle(children=["Custom geometries"])
        description = sw.Html(
            tag="p",
            class_="ma-2 grey--text text--darken-1",
            children=[
                "Add sub-areas inside your primary AOI. Drawn or imported "
                "shapes are checked against the primary AOI; admin sub-areas "
                "are guaranteed to fit by hierarchy."
            ],
        )

        # Compact list of actions. Each item carries an ``id`` attribute that
        # ``SeplanMap.on_draw`` reads to dispatch (admin → AdminAoiDialog,
        # new → Geoman on the map, import → ImportAoiDialog). Admin first
        # because it's the recommended path for admin-based primaries.
        self.item_admin = self._make_list_item("admin", "Admin sub-area")
        self.item_new = self._make_list_item(
            "new", cm.map.toolbar.draw_menu["new"]
        )
        self.item_import = self._make_list_item(
            "import", cm.map.toolbar.draw_menu["import"]
        )

        actions_list = v.List(
            dense=True,
            class_="py-0",
            children=[self.item_admin, self.item_new, self.item_import],
        )

        section_header = sw.Html(
            tag="h4",
            class_="ma-2 mt-4",
            children=["Saved custom geometries"],
        )
        # Independent table instance — observes ``map_.custom_layers`` so it
        # stays in sync without sharing state with ``CustomAoiDialog``.
        self.table = CustomGeometriesTable(self.map_)

        btn_close = TextBtn("Close", outlined=True)
        btn_close.on_event("click", lambda *_: self.close_dialog())
        action = sw.CardActions(children=[sw.Spacer(), btn_close])

        text = sw.CardText(
            children=[description, actions_list, section_header, self.table]
        )
        card = sw.Card(class_="ma-0", children=[title, text, action])
        self.children = [card]

    def _make_list_item(self, action_id: str, label: str) -> v.ListItem:
        """Build a clickable list item that dispatches via ``map_.on_draw``."""
        item = v.ListItem(
            attributes={"id": action_id},
            link=True,
            ripple=True,
            children=[
                v.ListItemContent(
                    children=[v.ListItemTitle(children=[label])]
                ),
            ],
        )
        item.on_event("click", self.map_.on_draw)
        return item


class CustomGeometriesTable(sw.Layout):
    def __init__(self, map_) -> None:
        self.class_ = "d-block"
        self.attributes = {"id": "custom_geometries_table"}
        self.no_items = cm.map.dialog.drawing.table.no_geometries

        # create the table
        super().__init__()

        self.map_ = map_

        # generate header using the translator
        headers = sw.Html(
            tag="tr",
            children=[
                sw.Html(tag="th", children=[title])
                for title in cp.custom_geom_table_headers.values()
            ],
        )

        self.tbody = sw.Html(attributes={"id": "tbody"}, tag="tbody", children=[])
        self.set_rows()

        # create the table
        self.table = sw.SimpleTable(
            dense=False,
            children=[
                sw.Html(tag="thead", children=[headers]),
                self.tbody,
            ],
        )

        self.children = [self.table]

        # add js behavior
        self.map_.observe(self.set_rows, "custom_layers")

    def set_rows(self, *args):
        """Add, remove or update rows in the table."""
        # We don't want to recreate all the elements of the table each time since
        # that's so expensive (specially the set_limits method)

        view_layers = [
            row.layer_id
            for row in self.tbody.children
            if isinstance(row, CustomGeometryRow)
        ]
        map_layers = [
            lyr.get("properties")["id"] for lyr in self.map_.custom_layers["features"]
        ]

        new_ids = [id_ for id_ in map_layers if id_ not in view_layers]
        old_ids = [id_ for id_ in view_layers if id_ not in map_layers]

        if new_ids:
            for new_id in new_ids:
                row = CustomGeometryRow(self.map_, new_id)
                # drop no items if it's in the table

                new_items = [
                    chld for chld in self.tbody.children if chld != self.no_items
                ] + [row]
                self.tbody.children = new_items

        elif old_ids:
            for old_id in old_ids:
                row_to_remove = self.tbody.get_children(attr="layer_id", value=old_id)[
                    0
                ]
                self.tbody.children = [
                    row
                    for row in self.tbody.children
                    if row not in [row_to_remove, self.no_items]
                ]

        if not self.tbody.children:
            self.tbody.children = [self.no_items]


class CustomGeometryRow(sw.Html):
    def __init__(self, map_, layer_id, **kwargs) -> None:
        self.tag = "tr"
        self.attributes = {"layer_id": layer_id}
        self.layer_id = layer_id

        super().__init__()

        self.map_ = map_

        # use layer_id to get the name of the geometry from the custom_layers dict
        for layer in self.map_.custom_layers["features"]:
            if layer["properties"]["id"] == layer_id:
                name = layer["properties"]["name"]

        self.delete_btn = cw.TableIcon(icon("trash-can"), self.layer_id)

        td_list = [
            sw.Html(tag="td", children=[self.delete_btn]),
            sw.Html(tag="td", children=[name]),
        ]

        super().__init__(tag="tr", children=td_list)

        # add js behaviour
        self.delete_btn.on_event("click", self.on_delete)

    def on_delete(self, widget, data, event):
        """Remove the line from the model and trigger table update."""
        self.map_.remove_custom_layer(self.layer_id)
