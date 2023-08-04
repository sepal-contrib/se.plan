import json
from pathlib import Path

import ee
from sepal_ui.scripts import utils

import component.parameter as cp
from component import model as cmod
from component.model.aoi_model import SeplanAoi
from component.scripts.seplan import Seplan

ee.Initialize()


class Recipe:
    aoi_model: SeplanAoi
    benefit_model: cmod.BenefitModel
    constraint_model: cmod.ConstraintModel
    cost_model: cmod.CostModel

    recipe_hash = "####### - sepal_ui_v_2 - ########"

    def __init__(self):
        self.seplan_aoi = SeplanAoi()
        self.benefit_model = cmod.BenefitModel()
        self.constraint_model = cmod.ConstraintModel()
        self.cost_model = cmod.CostModel()
        self.seplan = Seplan(
            self.seplan_aoi, self.benefit_model, self.constraint_model, self.cost_model
        )

    def load(self, path):
        """Load the recipe element in the different element of the app."""
        # cast to pathlib
        path = Path(path)

        # open the file and load the models
        with path.open() as f:
            data = json.loads(f.read())

        # TODO: check if the data is valid and raise errors if so

        # Check the data starts with the recipe hash and raise an error if not
        if data["recipe_hash"] != self.recipe_hash:
            raise ValueError("The recipe hash is not valid")

        # Check there's the right number of models inside the file
        # Check the models have all the right parameters

        # load the aoi_model
        self.seplan_aoi.import_data(data["aoi"])
        self.benefit_model.import_data(data["benefits"])
        self.constraint_model.import_data(data["constraints"])
        self.cost_model.import_data(data["costs"])

    def save(self, recipe_name):
        """Save the recipe in a json file with a timestamp."""
        # get the result folder

        res_dir = cp.result_dir / self.seplan_aoi.aoi_model.name
        res_dir.mkdir(exist_ok=True)

        # create the json file
        json_file = res_dir / f"{utils.normalize_str(recipe_name)}.json"

        with json_file.open("w") as f:
            data = {
                "aoi": self.seplan_aoi.export_data(),
                "benefits": self.benefit_model.export_data(),
                "constraints": self.constraint_model.export_data(),
                "costs": self.cost_model.export_data(),
            }

            json.dump(data, f)
