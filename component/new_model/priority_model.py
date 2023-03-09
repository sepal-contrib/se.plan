from sepal_ui import model
from traitlets import List, Int
import pandas as pd

from component import parameter as cp
from component.message import cm


class PriorityModel(model.Model):

    names = List([]).tag(sync=True)
    ids = List([]).tag(sync=True)
    themes = List([]).tag(sync=True)
    assets = List([]).tag(sync=True)
    descs = List([]).tag(sync=True)
    weights = List([]).tag(sync=True)
    units = List([]).tag(sync=True)
    updated = Int(0).tag(sync=True)

    def __init__(self):

        # get the default priority from the csv file
        _themes = pd.read_csv(cp.layer_list).fillna("").sort_values(by=["subtheme"])
        _themes = _themes[_themes.theme == "benefit"]

        for _, r in _themes.iterrows():
            self.names.append(cm.layers[r.layer_id].name)
            self.ids.append(r.layer_id)
            self.themes.append(r.subtheme)
            self.assets.append(r.gee_asset)
            self.descs.append(cm.layers[r.layer_id].detail)
            self.weights.append(4)
            self.units.append(r.unit)

        super().__init__()

    def remove_priority(self, name: str) -> None:
        """Remove a priority using its name"""

        idx = next(i for i, v in enumerate(self.names) if v == name)
        del self.names[idx]
        del self.ids[idx]
        del self.themes[idx]
        del self.assets[idx]
        del self.descs[idx]
        del self.weights[idx]
        del self.units[idx]

        self.updated += 1
