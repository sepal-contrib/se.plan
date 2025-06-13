import pandas as pd
from traitlets import List, observe

from component import parameter as cp
from component.message import cm
from component.model.questionnaire_model import QuestionnaireModel
from component.types import ConstraintLayerData

import logging

logger = logging.getLogger("SEPLAN")


class ConstraintModel(QuestionnaireModel):
    names = List([]).tag(sync=True)
    ids = List([]).tag(sync=True)
    themes = List([]).tag(sync=True)
    assets = List([]).tag(sync=True)
    descs = List([]).tag(sync=True)
    units = List([]).tag(sync=True)
    values = List([]).tag(sync=True)
    data_type = List([]).tag(sync=True)

    def __init__(self):
        # get the default constraint from the csv file
        _constraint = pd.read_csv(cp.layer_list).fillna("")
        _constraint = _constraint[_constraint.layer_id == "treecover_with_potential"]

        for _, r in _constraint.iterrows():
            self.themes.append(r.subtheme)
            self.names.append(cm.layers[r.layer_id].name)
            self.ids.append(r.layer_id)
            self.assets.append(r.gee_asset)
            self.descs.append(cm.layers[r.layer_id].detail)
            self.units.append(r.unit)
            self.values.append([0, 1])
            self.data_type.append(r.data_type)

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
        del self.units[idx]
        del self.values[idx]
        del self.data_type[idx]

        if update:
            logger.debug("updating from remove")
            self.updated += 1
        self.new_changes += 1

    def add(
        self,
        theme: str,
        name: str,
        id: str,
        asset: str,
        desc: str,
        unit: str,
        data_type: str,
    ) -> None:
        """add a constraint and trigger the update."""
        self.themes.append(theme)
        self.names.append(name)
        self.ids.append(id)
        self.assets.append(asset)
        self.descs.append(desc)
        self.units.append(unit)
        self.values.append([])
        self.data_type.append(data_type)
        logger.debug("updating from add")
        self.updated += 1
        self.new_changes += 1

    def update(
        self,
        theme: str,
        name: str,
        id: str,
        asset: str,
        desc: str,
        unit: str,
        data_type: str,
    ) -> None:
        """update an existing constraint metadata and trigger the update."""
        idx = self.get_index(id)

        self.themes[idx] = theme
        self.names[idx] = name
        self.ids[idx] = id
        self.assets[idx] = asset
        self.descs[idx] = desc
        self.units[idx] = unit
        self.data_type[idx] = data_type
        logger.debug("updating from update")
        self.updated += 1
        self.new_changes += 1

    def update_value(self, id: str, value: list) -> None:
        """Update the value of a specific constraint."""
        idx = self.get_index(id)

        self.values[idx] = value
        self.new_changes += 1

    def reset(self):
        """Reset the model to its default values."""
        self.names = []
        self.ids = []
        self.themes = []
        self.assets = []
        self.descs = []
        self.units = []
        self.values = []
        self.data_type = []

        self.__init__()
        logger.debug("updating from reset")
        self.updated += 1
        self.new_changes = 0

    @observe("updated")
    def _on_update(self, *_):
        logger.debug("######## updated ########")

    def get_layer_data(self, layer_id: str) -> ConstraintLayerData:
        """Return the data of a specific layer."""
        idx = self.get_index(layer_id)
        return {
            "id": self.ids[idx],
            "name": self.names[idx],
            "asset": self.assets[idx],
            "desc": self.descs[idx],
            "unit": self.units[idx],
            "value": self.values[idx],
            "data_type": self.data_type[idx],
        }
