import numpy as np
import pandas as pd
from sepal_ui import model
from traitlets import Int, List

from component import parameter as cp
from component.message import cm


class ConstraintModel(model.Model):
    names = List([]).tag(sync=True)
    ids = List([]).tag(sync=True)
    themes = List([]).tag(sync=True)
    assets = List([]).tag(sync=True)
    descs = List([]).tag(sync=True)
    units = List([]).tag(sync=True)
    values = List([]).tag(sync=True)

    updated = Int(0).tag(sync=True)
    validated = Int(0).tag(sync=True)

    def __init__(self):
        # get the default costs from the csv file
        _costs = pd.read_csv(cp.layer_list).fillna("")
        _costs = _costs[_costs.layer_id == "treecover_with_potential"]

        for _, r in _costs.iterrows():
            self.themes.append(r.subtheme)
            self.names.append(cm.layers[r.layer_id].name)
            self.ids.append(r.layer_id)
            self.assets.append(r.gee_asset)
            self.descs.append(cm.layers[r.layer_id].detail)
            self.units.append(r.unit)
            self.values.append([1, 1])

        super().__init__()

    def remove_constraint(self, id: str) -> None:
        """Remove a constraint using its name."""
        idx = self.get_index(id)

        del self.names[idx]
        del self.ids[idx]
        del self.themes[idx]
        del self.assets[idx]
        del self.descs[idx]
        del self.units[idx]
        del self.values[idx]

        self.updated += 1

    def add_constraint(
        self, theme: str, name: str, id: str, asset: str, desc: str, unit: str
    ) -> None:
        """add a constraint and trigger the update."""
        self.themes.append(theme)
        self.names.append(name)
        self.ids.append(id)
        self.assets.append(asset)
        self.descs.append(desc)
        self.units.append(unit)
        self.values.append([np.iinfo(np.int16).min, np.iinfo(np.int16).max])

        self.updated += 1

    def update_constraint(
        self, theme: str, name: str, id: str, asset: str, desc: str, unit: str
    ) -> None:
        """update an existing constraint metadata and trigger the update."""
        idx = self.get_index(id)

        self.themes[idx] = theme
        self.names[idx] = name
        self.ids[idx] = id
        self.assets[idx] = asset
        self.descs[idx] = desc
        self.units[idx] = unit

        self.updated += 1

    def update_value(self, id: str, value: list) -> None:
        """Update the value of a specific constraint."""
        idx = self.get_index(id)
        self.values[idx] = value

        # self.updated += 1

    def get_index(self, id: str) -> int:
        """get the index of the searched layer id."""
        return next(i for i, v in enumerate(self.ids) if v == id)
