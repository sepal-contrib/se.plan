from sepal_ui import sepalwidgets as sw
import pandas as pd

from component.message import cm
from component import parameter as cp


class PriorityRow(sw.Html):
    def __init__(self, layer_id: str, theme: str) -> None:

        # create the crud interface
        edit_btn = sw.Icon(children=["fa-solid fa-pencil"])
        delete_btn = sw.Icon(children=["fa-solid fa-trash-can"])
        edit_btn.class_list.add("mr-2")
        edit_btn.small = delete_btn.small = True
        edit_btn.attributes = delete_btn.attributes = {"data-layer": layer_id}

        # create the checkbox_list
        self.check_list = []
        for i in range(5):
            attr = {"data-label": layer_id, "data-val": i}
            check = sw.Checkbox(attributes=attr, v_model=i == 4)
            self.check_list.append(check)

        td_list = [
            sw.Html(tag="td", children=[edit_btn, delete_btn]),
            sw.Html(tag="td", children=[theme]),
            sw.Html(tag="td", children=[layer_id]),
            *[sw.Html(tag="td", children=[e]) for e in self.check_list],
        ]

        super().__init__(tag="tr", children=td_list)

        # add js behaviour
        [e.observe(self._on_check_change, "v_model") for e in self.check_list]

    def _on_check_change(self, change):

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


class PriorityTable(sw.SimpleTable):
    def __init__(self) -> None:

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

        # create the table
        super().__init__(
            dense=True,
            children=[
                sw.Html(tag="thead", children=[headers]),
                self.tbody,
            ],
        )

        # set the default lines with all the default priorities
        _themes = pd.read_csv(cp.layer_list).fillna("").sort_values(by=["subtheme"])
        _themes = _themes[_themes.theme == "benefit"]

        for _, r in _themes.iterrows():
            self.add_row(r.layer_id, r.subtheme)

    def add_row(self, layer_id: str, theme: str) -> None:
        """Add a row to the table based on the layer_id"""

        # create a new row
        row = [PriorityRow(layer_id, theme)]
        children = self.tbody.children.copy() + row
        self.tbody.children = children

        return
