import json
from pathlib import Path
from typing import Literal

import ee
from traitlets import Dict, HasTraits

import component.parameter as cp
from component import model as cmod
from component.model.aoi_model import SeplanAoi
from component.scripts import validation
from component.scripts.seplan import Seplan

ee.Initialize()


class Recipe(HasTraits):
    # Set types
    aoi_model: SeplanAoi
    benefit_model: cmod.BenefitModel
    constraint_model: cmod.ConstraintModel
    cost_model: cmod.CostModel

    # Define traits
    build_state = Dict(
        {
            "aoi": "waiting",
            "questionnaire": "waiting",
            "map": "waiting",
            "dashboard": "waiting",
        }
    ).tag(sync=True)

    def load_model(self):
        """Define all the models required by the module."""
        self.seplan_aoi = SeplanAoi()
        self.benefit_model = cmod.BenefitModel()
        self.constraint_model = cmod.ConstraintModel()
        self.cost_model = cmod.CostModel()
        self.seplan = Seplan(
            self.seplan_aoi, self.benefit_model, self.constraint_model, self.cost_model
        )

    def load(self, recipe_path: str):
        """Load the recipe element in the different element of the app."""
        # This is not necessary since the recipe path is already validated from the origin
        # but I want to keep it here if I want to call the load function from somewhere else
        recipe_path = Path(validation.validate_recipe(recipe_path))
        with recipe_path.open() as f:
            data = json.loads(f.read())

        # load the aoi_model
        self.seplan_aoi.import_data(data["aoi"])
        self.benefit_model.import_data(data["benefits"])
        self.constraint_model.import_data(data["constraints"])
        self.cost_model.import_data(data["costs"])

    def save(self, recipe_name: str):
        """Save the recipe in a json file with a timestamp."""
        # get the result folder

        res_dir = cp.result_dir / self.seplan_aoi.aoi_model.name
        res_dir.mkdir(exist_ok=True)

        recipe_path = Path(recipe_name)

        # add .json if not present
        if recipe_path.suffix != ".json":
            recipe_path = recipe_path.with_suffix(".json")

        # create the json file
        json_file = res_dir / f"{str(recipe_path)}"

        with json_file.open("w") as f:
            data = {
                "signature": cp.recipe_signature,
                "data": {
                    "aoi": self.seplan_aoi.export_data(),
                    "benefits": self.benefit_model.export_data(),
                    "constraints": self.constraint_model.export_data(),
                    "costs": self.cost_model.export_data(),
                },
            }

            json.dump(data, f, indent=4)

    def reset(self):
        """Reset the recipe to its default values."""
        # We can either load a default known recipe, or trigger a reset of all the models

        self.load(cp.default_recipe)

    def set_state(
        self,
        component: Literal["aoi", "questionnaire", "map", "dashboard"],
        value: Literal["building", "done", "waiting"],
    ):
        """Set the done status of a component to True or False."""
        tmp_state = self.build_state.copy()
        tmp_state[component] = value
        self.build_state = tmp_state
