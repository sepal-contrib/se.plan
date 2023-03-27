from sepal_ui import model
from traitlets import List, Int
import pandas as pd

from component import parameter as cp
from component.message import cm


class CostModel(model.Model):

    names = List([]).tag(sync=True)
    ids = List([]).tag(sync=True)
    assets = List([]).tag(sync=True)
    descs = List([]).tag(sync=True)
    units = List([]).tag(sync=True)

    updated = Int(0).tag(sync=True)

    def __init__(self):

        # get the default costs from the csv file
        _themes = pd.read_csv(cp.layer_list).fillna("")
        _themes = _themes[_themes.theme == "cost"]

        for _, r in _themes.iterrows():
            self.names.append(cm.layers[r.layer_id].name)
            self.ids.append(r.layer_id)
            self.assets.append(r.gee_asset)
            self.descs.append(cm.layers[r.layer_id].detail)
            self.units.append(r.unit)

        super().__init__()

    def remove_cost(self, id: str) -> None:
        """Remove a cost using its id"""

        idx = self.get_index(id)

        del self.names[idx]
        del self.ids[idx]
        del self.assets[idx]
        del self.descs[idx]
        del self.units[idx]

        self.updated += 1

    def add_cost(self, name: str, id: str, asset: str, desc: str, unit: str) -> None:
        """add a cost and trigger the update"""

        self.names.append(name)
        self.ids.append(id)
        self.assets.append(asset)
        self.descs.append(desc)
        self.units.append(unit)

        self.updated += 1

    def update_cost(self, name: str, id: str, asset: str, desc: str, unit: str) -> None:
        """update an existing cost metadata and trigger the update"""

        idx = self.get_index(id)

        self.names[idx] = name
        self.ids[idx] = id
        self.assets[idx] = asset
        self.descs[idx] = desc
        self.units[idx] = unit

        self.updated += 1

    def get_index(self, id: str) -> int:
        """get the index of the searched layer id"""

        return next(i for i, v in enumerate(self.ids) if v == id)
