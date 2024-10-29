import pandas as pd
from traitlets import List

from component import parameter as cp
from component.message import cm
from component.model.questionnaire_model import QuestionnaireModel
from component.types import BenefitLayerData


class BenefitModel(QuestionnaireModel):
    names = List([]).tag(sync=True)
    ids = List([]).tag(sync=True)
    themes = List([]).tag(sync=True)
    assets = List([]).tag(sync=True)
    descs = List([]).tag(sync=True)
    weights = List([]).tag(sync=True)
    units = List([]).tag(sync=True)

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

    def remove(self, id: str, update=True) -> None:
        """Remove a constraint using its name.

        Args:
            id (str): the id of the constraint to remove
            update (bool, optional): trigger the update. Defaults to True.
                I dont' want to update the whole table if one asset failed
                to be added.
        """
        idx = self.get_index(id)

        del self.names[idx]
        del self.ids[idx]
        del self.themes[idx]
        del self.assets[idx]
        del self.descs[idx]
        del self.weights[idx]
        del self.units[idx]

        if update:
            self.updated += 1
        self.new_changes += 1

    def add(
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
        self.new_changes += 1

    def update(
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
        self.new_changes += 1

    def update_value(self, id: str, value: list) -> None:
        """Update the value of a specific benefit."""
        idx = self.get_index(id)

        self.weights[idx] = value
        self.new_changes += 1

    def reset(self):
        """Reset the model to its default values."""
        self.names = []
        self.ids = []
        self.themes = []
        self.assets = []
        self.descs = []
        self.weights = []
        self.units = []

        self.__init__()

        self.updated += 1
        self.new_changes = 0

    def get_layer_data(self, layer_id: str) -> BenefitLayerData:
        """Return the data of a specific layer."""
        idx = self.get_index(layer_id)
        return {
            "id": self.ids[idx],
            "name": self.names[idx],
            "asset": self.assets[idx],
            "desc": self.descs[idx],
            "unit": self.units[idx],
            "theme": self.themes[idx],
            "weight": self.weights[idx],
        }
