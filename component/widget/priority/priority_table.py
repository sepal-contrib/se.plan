import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

from component import parameter as cp
from component.message import cm
from component.model.priority_model import PriorityModel
from component.widget import custom_widgets as cw

from .priority_dialog import PriorityDialog


class PriorityRow(sw.Html):
    _DEFAULT_THEMES = pd.read_csv(cp.layer_list).layer_id

    def __init__(self, model: PriorityModel, idx: int, dialog: PriorityDialog) -> None:
        # get the model as a member
        self.model = model
        self.dialog = dialog

        # extract information from the model
        name = self.model.names[idx]
        layer_id = self.model.ids[idx]
        theme = self.model.themes[idx]
        weight = self.model.weights[idx]

        # create the crud interface
        self.edit_btn = cw.TableIcon("fa-solid fa-pencil", layer_id)
        self.delete_btn = cw.TableIcon("fa-solid fa-trash-can", layer_id)
        self.edit_btn.class_list.add("mr-2")

        # create the checkbox_list
        self.check_list = []
        for i in range(5):
            attr = {"data-label": layer_id, "data-val": i}
            check = sw.Checkbox(attributes=attr, v_model=i == weight)
            self.check_list.append(check)

        td_list = [
            sw.Html(tag="td", children=[self.edit_btn, self.delete_btn]),
            sw.Html(tag="td", children=[cm.subtheme[theme]]),
            sw.Html(tag="td", children=[name]),
            *[sw.Html(tag="td", children=[e]) for e in self.check_list],
        ]

        super().__init__(tag="tr", children=td_list)

        # add js behaviour
        [e.observe(self.on_check_change, "v_model") for e in self.check_list]
        self.delete_btn.on_event("click", self.on_delete)
        self.edit_btn.on_event("click", self.on_edit)

    def on_check_change(self, change):
        # if checkbox is unique and change == false recheck
        if change["new"] is False:
            unique = True
            for check in self.check_list:
                if check.v_model is True:
                    unique = False
                    break

            change["owner"].v_model = unique

        else:
            # uncheck all the others in the line
            for check in self.check_list:
                if check != change["owner"]:
                    check.v_model = False

        return

    def on_delete(self, widget, data, event):
        """remove the line from the model and trigger table update."""
        self.model.remove_priority(widget.attributes["data-layer"])

    @sd.switch("loading", on_widgets=["dialog"])
    def on_edit(self, widget, data, event):
        """open the dialog with the data contained in the model."""
        idx = self.model.get_index(widget.attributes["data-layer"])

        self.dialog.fill(
            theme=self.model.themes[idx],
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
            unit=self.model.units[idx],
        )
        # clean any previous errors
        self.dialog.w_alert.reset()
        self.dialog.value = True


class PriorityTable(sw.Layout):
    def __init__(self, model: PriorityModel, dialog: PriorityDialog) -> None:
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
                sw.Html(tag="th", children=[cm.benefits.table.theme]),
                sw.Html(tag="th", children=[cm.benefits.table.indicator]),
                *[
                    sw.Html(tag="th", children=[lbl])
                    for lbl in cm.benefits.table.labels
                ],
            ],
        )

        self.tbody = sw.Html(tag="tbody", children=[])
        self.set_rows()

        self.table = sw.SimpleTable(
            dense=True,
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
            row = PriorityRow(self.model, i, self.dialog)
            rows.append(row)
        self.tbody.children = rows
