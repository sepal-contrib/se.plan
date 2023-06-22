import pandas as pd
from sepal_ui import sepalwidgets as sw

from component import parameter as cp
from component.message import cm


class CostTile(sw.Tile):
    _COSTS = pd.read_csv(cp.layer_list).fillna("")
    _COSTS = _COSTS[_COSTS.theme == "cost"]

    def __init__(self):
        # name the tile
        title = cm.cost.title
        id_ = "nested_widget"

        # build the cost table
        rows, self.btn_list = [], []
        for id_ in self._COSTS.layer_id:
            edit_btn = sw.Icon(children=["mdi-pencil"], _metadata={"layer": id_})
            self.btn_list.append(edit_btn)
            td = [
                sw.Html(tag="td", children=[edit_btn]),
                sw.Html(tag="td", children=[getattr(cm.layers, id_).name]),
                sw.Html(tag="td", children=[getattr(cm.layers, id_).detail]),
            ]
            rows.append(sw.Html(tag="tr", children=td))

        th = [
            sw.Html(tag="th", children=[cm.cost.table.action]),
            sw.Html(tag="th", children=[cm.cost.table.cost]),
            sw.Html(tag="th", children=[cm.cost.table.description]),
        ]
        header = sw.Html(tag="thead", children=th)

        body = sw.Html(tag="tbody", children=rows)

        self.table = sw.SimpleTable(children=[header, body])

        super().__init__(id_, title, inputs=[self.table])
