from copy import deepcopy

from matplotlib import pyplot as plt
from matplotlib.colors import to_hex
from sepal_ui import sepalwidgets as sw
from sepal_ui.aoi.aoi_model import AoiModel

import component.parameter as cp
from component.message import cm
from component.widget import custom_widgets as cw
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn

from .map import SeplanMap


class CustomAoiDialog(BaseDialog):
    feature: dict = None
    "feature collection of new geometry imported from ImportAoiDialog."

    def __init__(self, map_: SeplanMap):
        super().__init__()
        self.attributes = {"id": "custom_aoi_dialog"}
        self.map_ = map_

        # create the widgets
        self.btn = TextBtn(cm.map.dialog.drawing.btn, gliph="mdi-check")
        title = sw.CardTitle(children=[cm.map.dialog.drawing.title])
        # Create table to show the custom geometries
        table = CustomGeometriesTable(self.map_)
        self.w_name = sw.TextField(
            label=cm.map.dialog.drawing.label, v_model=None, class_="mr-2"
        )

        self.save_input = sw.Flex(
            class_="d-flex align-center",
            children=[
                self.w_name,
                self.btn,
            ],
        )
        text = sw.CardText(children=[table, self.save_input])
        btn_cancel = TextBtn(cm.map.dialog.drawing.cancel)
        action = sw.CardActions(children=[sw.Spacer(), btn_cancel])
        card = sw.Card(class_="ma-0", children=[title, text, action])

        self.children = [card]

        # add js behavior
        btn_cancel.on_event("click", self.on_cancel)
        self.btn.on_event("click", self.on_save_geom)

        self.map_.observe(self.on_new_geom, "new_geom")

    def on_save_geom(self, *_):
        """Updates map_.custom_layers with the new geometry."""
        # Get all the fc in the map_.dc, there should be only one

        if self.feature:
            features = self.feature["features"]

            # Increase the new_geom counter but don't trigger the event
            self.map_.unobserve(self.on_new_geom, "new_geom")
            self.map_.new_geom += 1
            self.map_.observe(self.on_new_geom, "new_geom")

        else:
            features = self.map_.dc.to_json()["features"]

        geom_number = self.map_.new_geom
        aoi_color = to_hex(plt.cm.tab10(geom_number))
        style = {
            **cp.aoi_style,
            "color": aoi_color,
            "fillColor": aoi_color,
        }

        for feature in features:
            feature["properties"]["id"] = geom_number
            feature["properties"]["name"] = self.w_name.v_model
            feature["properties"]["style"] = style
            feature["properties"]["hover_style"] = {
                **style,
                "fillOpacity": 0.4,
                "weight": 2,
            }
        current_feats = deepcopy(self.map_.custom_layers)
        current_feats["features"] += features

        # Trigger the change in the custom_layers dict
        self.map_.custom_layers = current_feats

        # Remove all the geometries from the map_.dc and close the dialog
        self.on_cancel()

    def on_cancel(self, *_):
        """Remove all the geometries from the map_.dc."""
        self.map_.dc.clear()

        # Clear any feature that was selected
        self.feature = None

        # Close the dialog
        self.close_dialog()

    def open_dialog(
        self,
        new_geom: bool,
        *_,
    ):
        """Open dialog in two different ways."""
        # hide save element and only show table
        self.save_input.show() if new_geom else self.save_input.hide()

        super().open_dialog()

    def on_new_geom(self, *_, feature_collection: dict = None, name: str = None):
        """Read the aoi and give an default name.

        It will manage the new geometries drawn by the user and the custom ones
        imported by the user (using ImportAoiDialog)

        Args:
            aoi_model (AoiModel): Aoi Model when using the import aoi dialog
        """
        # Count the number of geometries in map_.custom_layers
        index = len(self.map_.custom_layers["features"]) + 1

        if not feature_collection:
            aoi_name = f"Custom AOI {index}"
        else:
            aoi_name = f"Custom_{name}"
            self.feature = feature_collection

        self.w_name.v_model = aoi_name
        self.open_dialog(new_geom=True)


class CustomGeometriesTable(sw.Layout):
    def __init__(self, map_: SeplanMap) -> None:
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

        self.children = [
            self.table,
        ]

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

        # self.delete_btn = cw.TableIcon("fa-solid fa-trash-can", self.layer_id)
        self.delete_btn = cw.TableIcon("mdi-trash-can", self.layer_id)

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
