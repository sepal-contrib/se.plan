import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

from component import parameter as cp
from component.message import cm
from component.model.cost_model import CostModel
from component.widget import custom_widgets as cw

from .cost_dialog import CostDialog


class CostRow(sw.Html):
    _DEFAULT_LAYERS = pd.read_csv(cp.layer_list).layer_id

    def __init__(self, model: CostModel, idx: int, dialog: CostDialog) -> None:
        # get the model as a member
        self.model = model
        self.dialog = dialog

        # extract information from the model
        name = self.model.names[idx]
        layer_id = self.model.ids[idx]

        # create the crud interface
        self.edit_btn = cw.TableIcon("fa-solid fa-pencil", layer_id)
        self.delete_btn = cw.TableIcon("fa-solid fa-trash-can", layer_id)
        self.edit_btn.class_list.add("mr-2")

        td_list = [
            sw.Html(tag="td", children=[self.edit_btn, self.delete_btn]),
            sw.Html(tag="td", children=[name]),
        ]

        super().__init__(tag="tr", children=td_list)

        # add js behaviour
        self.delete_btn.on_event("click", self.on_delete)
        self.edit_btn.on_event("click", self.on_edit)

    def on_delete(self, widget, data, event):
        """remove the line from the model and trigger table update."""
        self.model.remove_cost(widget.attributes["data-layer"])

    @sd.switch("loading", on_widgets=["dialog"])
    def on_edit(self, widget, data, event):
        """open the dialog with the data contained in the model."""
        idx = self.model.get_index(widget.attributes["data-layer"])

        self.dialog.fill(
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
        )

        self.dialog.value = True


class CostTable(sw.Layout):
    def __init__(self, model: CostModel, dialog: CostDialog) -> None:
        # save the model and dialog as a member
        self.model = model
        self.dialog = dialog
        self.toolbar = cw.ToolBar(model, dialog)

        # create the table
        super().__init__()

        self.class_ = "d-block"

        # generate header using the translator
        headers = sw.Html(
            tag="tr",
            children=[
                sw.Html(tag="th", children=[cm.benefits.table.action]),
                sw.Html(tag="th", children=[cm.benefits.table.indicator]),
            ],
        )

        self.tbody = sw.Html(tag="tbody", children=[])
        self.set_rows()

        # create the table
        self.table = sw.SimpleTable(
            dense=False,
            children=[
                sw.Html(tag="thead", children=[headers]),
                self.tbody,
            ],
        )

        self.children = [self.toolbar, self.table]

        # add js behavior
        self.model.observe(self.set_rows, "updated")

    def set_rows(self, *args):
        rows = []
        for i, _ in enumerate(self.model.names):
            row = CostRow(self.model, i, self.dialog)
            rows.append(row)
        self.tbody.children = rows
