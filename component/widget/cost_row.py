import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

from component import parameter as cp
from component.model import CostModel
from component.widget import custom_widgets as cw
from component.widget.cost_dialog import CostDialog


class CostRow(sw.Html):
    _DEFAULT_LAYERS = pd.read_csv(cp.layer_list).layer_id

    def __init__(
        self, model: CostModel, layer_id: str, dialog: CostDialog, **kwargs
    ) -> None:
        self.tag = "tr"
        self.attributes = {"layer_id": layer_id}

        super().__init__()

        # get the model as a member
        self.model = model
        self.dialog = dialog

        idx = model.get_index(id=layer_id)

        # extract information from the model
        self.name = self.model.names[idx]
        self.layer_id = self.model.ids[idx]

        self.update_view()

    def update_view(self):
        """Create the view of the widget based on the model."""
        # create the crud interface
        self.edit_btn = cw.TableIcon("fa-solid fa-pencil", self.layer_id)
        self.delete_btn = cw.TableIcon("fa-solid fa-trash-can", self.layer_id)
        self.edit_btn.class_list.add("mr-2")

        td_list = [
            sw.Html(tag="td", children=[self.edit_btn, self.delete_btn]),
            sw.Html(tag="td", children=[self.name]),
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
