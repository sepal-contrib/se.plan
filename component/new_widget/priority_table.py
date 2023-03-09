from sepal_ui import sepalwidgets as sw
import pandas as pd

from component.message import cm
from component import parameter as cp
from component import new_model as cmod


class TableIcon(sw.Icon):
    def __init__(self, gliph: str, name: str):

        super().__init__(
            children=[gliph],
            icon=True,
            small=True,
            attributes={"data-layer": name},
            style_="font-family: 'Font Awesome 6 Free';",
        )


class PriorityRow(sw.Html):

    _DEFAULT_THEMES = pd.read_csv(cp.layer_list).layer_id

    def __init__(self, model: cmod.PriorityModel, idx: int) -> None:

        # get the model as a member
        self.model = model

        # extract information from the model
        name = self.model.names[idx]
        layer_id = self.model.ids[idx]
        theme = self.model.themes[idx]
        weight = self.model.weights[idx]

        # create the crud interface
        self.edit_btn = TableIcon("fa-solid fa-pencil", layer_id)
        self.delete_btn = TableIcon("fa-solid fa-trash-can", layer_id)
        self.edit_btn.class_list.add("mr-2")

        # hide the delete btn for default layers
        if self._DEFAULT_THEMES.str.contains(layer_id).any():
            self.delete_btn.hide()

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

    def on_check_change(self, change):

        # if checkbox is unique and change == false recheck
        if change["new"] == False:
            unique = True
            for check in self.check_list:
                if check.v_model == True:
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
        """remove the line from the model and trigger table update"""

        self.model.remove_priority(widget.attributes["data-layer"])


class PriorityTable(sw.SimpleTable):
    def __init__(self, model: cmod.PriorityModel) -> None:

        # save the model as a member
        self.model = model

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

        # create the table
        super().__init__(
            dense=True,
            children=[
                sw.Html(tag="thead", children=[headers]),
                self.tbody,
            ],
        )

        # add js behavior
        self.model.observe(self.set_rows, "updated")

    def set_rows(self, *args):

        rows = []
        for i, _ in enumerate(self.model.names):
            row = PriorityRow(self.model, i)
            rows.append(row)
        self.tbody.children = rows
