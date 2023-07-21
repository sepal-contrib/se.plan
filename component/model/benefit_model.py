import pandas as pd
from sepal_ui import model
from traitlets import Int, List

from component import parameter as cp
from component.message import cm


class BenefitModel(model.Model):
    names = List([]).tag(sync=True)
    ids = List([]).tag(sync=True)
    themes = List([]).tag(sync=True)
    assets = List([]).tag(sync=True)
    descs = List([]).tag(sync=True)
    weights = List([]).tag(sync=True)
    units = List([]).tag(sync=True)

    updated = Int(0).tag(sync=True)
    validated = Int(0).tag(sync=True)

    def __init__(self):
        # get the default benefit from the csv file
        _themes = pd.read_csv(cp.layer_list).fillna("").sort_values(by=["subtheme"])
        _themes = _themes[_themes.theme == "benefit"]

        for _, row in _themes.iterrows():
            self.names.append(cm.layers[row.layer_id].name)
            self.ids.append(row.layer_id)
            self.themes.append(row.subtheme)
            self.assets.append(row.gee_asset)
            self.descs.append(cm.layers[row.layer_id].detail)
            self.weights.append(4)
            self.units.append(row.unit)

        super().__init__()

    def remove_benefit(self, id: str) -> None:
        """Remove a benefit using its name."""
        idx = self.get_index(id)

        del self.names[idx]
        del self.ids[idx]
        del self.themes[idx]
        del self.assets[idx]
        del self.descs[idx]
        del self.weights[idx]
        del self.units[idx]

        self.updated += 1

    def add_benefit(
        self, theme: str, name: str, id: str, asset: str, desc: str, unit: str
    ) -> None:
        """add a benefit and trigger the update."""
        self.themes.append(theme)
        self.names.append(name)
        self.ids.append(id)
        self.assets.append(asset)
        self.descs.append(desc)
        self.weights.append(4)
        self.units.append(unit)

        self.updated += 1

    def update_benefit(
        self, theme: str, name: str, id: str, asset: str, desc: str, unit: str
    ) -> None:
        """update an existing benefit metadata and trigger the update."""
        idx = self.get_index(id)

        self.themes[idx] = theme
        self.names[idx] = name
        self.ids[idx] = id
        self.assets[idx] = asset
        self.descs[idx] = desc
        self.units[idx] = unit

        self.updated += 1

    def update_value(self, id: str, value: list) -> None:
        """Update the value of a specific benefit."""
        idx = self.get_index(id)
        self.weights[idx] = value

    def get_index(self, id: str) -> int:
        """get the index of the searched layer id."""
        return next(i for i, v in enumerate(self.ids) if v == id)
