import pandas as pd
from sepal_ui import sepalwidgets as sw

from component.message import cm
from component import parameter as cp


class CostTile(sw.Tile):

    _COSTS = pd.read_csv(cp.layer_list).fillna("")
    _COSTS = _COSTS[_COSTS.theme == "costs"]

    def __init__(self):

        # name the tile
        title = cm.cost.title
        id_ = "nested_widget"

        # build the cost table
        rows, self.btn_list = [], []
        for _, lr in self._COSTS.iterrows():
            edit_btn = sw.Icon(
                children=["mdi-pencil"], _metadata={"layer": lr.layer_id}
            )
            self.btn_list.append(edit_btn)
            rows.append(
                sw.Html(
                    tag="tr",
                    children=[
                        sw.Html(tag="td", children=[edit_btn]),
                        sw.Html(tag="td", children=[lr.layer_name]),
                        sw.Html(tag="td", children=[lr.layer_info]),
                    ],
                )
            )

        header = sw.Html(
            tag="thead",
            children=[
                sw.Html(tag="th", children=[cm.cost.table.action]),
                sw.Html(tag="th", children=[cm.cost.table.cost]),
                sw.Html(tag="th", children=[cm.cost.table.description]),
            ],
        )

        self.table = sw.SimpleTable(
            children=[header, sw.Html(tag="tbody", children=rows)]
        )

        super().__init__(id_, title, inputs=[self.table])
