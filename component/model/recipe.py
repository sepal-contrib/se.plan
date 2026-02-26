from typing import Union
from component.scripts.file_handler import save_file
from pathlib import Path

from sepal_ui.scripts.warning import SepalWarning
from sepal_ui.scripts.gee_interface import GEEInterface
from traitlets import HasTraits, Int, Unicode, observe, List as TraitsList

import component.parameter as cp
from component import model as cmod
from component.message import cm
from component.model.aoi_model import SeplanAoi
from component.scripts import validation
from component.scripts.seplan import Seplan

import logging

logger = logging.getLogger("SEPLAN")


class Recipe(HasTraits):
    # Set types
    aoi_model: SeplanAoi
    benefit_model: cmod.BenefitModel
    constraint_model: cmod.ConstraintModel
    cost_model: cmod.CostModel

    new_changes = Int().tag(sync=True)
    """A counter that is incremented every time any of the app model changes. This trait is linked to the app_model, so we can show messaages on the app_bar"""

    recipe_session_path = Unicode("", allow_none=True).tag(sync=True)
    """The path to the recipe session file. This value will come from the recipe view, it will be used by the export csv function and to create the names of the assets to export"""

    def __init__(
        self,
        sepal_session=None,
        gee_interface: GEEInterface = None,
        folder=None,
        **delete_aoi,
    ):
        super().__init__()

        self.seplan_aoi = SeplanAoi(
            gee_interface=gee_interface, folder=folder, **delete_aoi
        )
        self.benefit_model = cmod.BenefitModel()
        self.constraint_model = cmod.ConstraintModel()
        self.cost_model = cmod.CostModel()
        self.dash_model = cmod.DashboardModel()
        self.sepal_session = sepal_session
        self.gee_interface = gee_interface
        self.seplan = Seplan(
            self.seplan_aoi, self.benefit_model, self.constraint_model, self.cost_model
        )

        # link the new_changes counter to the models
        self.seplan_aoi.observe(self.update_changes, "updated")
        # Icall them "new_changes" because there's another "updated" trait that is
        # used to trigger the update of the view of these models.
        self.benefit_model.observe(self.update_changes, "new_changes")
        self.constraint_model.observe(self.update_changes, "new_changes")
        self.cost_model.observe(self.update_changes, "new_changes")

        logger.debug(
            f"sepal_session----{str(sepal_session)}",
        )

    def update_changes(self, change):
        """Increment the new_changes counter by 1."""
        self.new_changes += 1

    def load(self, recipe_path: str):
        """Load the recipe element in the different element of the app.

        Returns:
            self if successful, or ValidationResult if validation errors found
        """
        logger.debug(f"Loading recipe: {recipe_path}....{self.sepal_session}")

        recipe_path, data = validation.read_recipe_data(
            recipe_path, sepal_session=self.sepal_session
        )

        # Validate all data types BEFORE importing to models
        validation_result = validation.validate_recipe_data(
            benefits=data["benefits"],
            constraints=data["constraints"],
            costs=data["costs"],
        )

        # If validation found errors, return the result WITHOUT loading
        if validation_result.has_errors:
            logger.warning(
                f"Recipe validation failed with {validation_result.total_errors} errors"
            )
            # Store the raw data and validation result for UI to handle
            validation_result.raw_data = data
            validation_result.recipe_path = str(recipe_path)  # Convert to string
            return validation_result

        # Only load if validation passed
        self.recipe_session_path = str(recipe_path)

        # load the aoi_model
        self.seplan_aoi.import_data(data["aoi"])
        self.benefit_model.import_data(data["benefits"])
        self.constraint_model.import_data(data["constraints"])
        self.cost_model.import_data(data["costs"])

        self.new_changes = 0

        return self

    async def load_async(self, recipe_path: str):
        """Load the recipe element in the different element of the app.

        Returns:
            self if successful, or ValidationResult if validation errors found
        """
        logger.debug(f"Loading recipe: {recipe_path}....{self.sepal_session}")

        recipe_path, data = validation.read_recipe_data(
            recipe_path, sepal_session=self.sepal_session
        )

        # Validate all data types BEFORE importing to models
        validation_result = validation.validate_recipe_data(
            benefits=data["benefits"],
            constraints=data["constraints"],
            costs=data["costs"],
        )

        # If validation found errors, return the result WITHOUT loading
        if validation_result.has_errors:
            logger.warning(
                f"Recipe validation failed with {validation_result.total_errors} errors"
            )
            # Store the raw data and validation result for UI to handle
            validation_result.raw_data = data
            validation_result.recipe_path = str(recipe_path)  # Convert to string
            return validation_result

        # Only load if validation passed
        self.recipe_session_path = str(recipe_path)

        # load the aoi_model
        await self.seplan_aoi.import_data_async(data["aoi"])
        self.benefit_model.import_data(data["benefits"])
        self.constraint_model.import_data(data["constraints"])
        self.cost_model.import_data(data["costs"])

        self.new_changes = 0

        return self

    def load_sanitized(self, data: dict, recipe_path: str):
        """Load sanitized recipe data after user accepts fixes.

        This is called after validation found errors and the user chose to continue
        with sanitized data.

        Args:
            data: Sanitized recipe data dictionary
            recipe_path: Path to the recipe file
        """
        logger.debug(f"Loading sanitized recipe data from: {recipe_path}")

        self.recipe_session_path = str(recipe_path)

        # Load all the data (already sanitized)
        self.seplan_aoi.import_data(data["aoi"])
        self.benefit_model.import_data(data["benefits"])
        self.constraint_model.import_data(data["constraints"])
        self.cost_model.import_data(data["costs"])

        self.new_changes = 0

        logger.info("Sanitized recipe loaded successfully")
        return self

    def save(self, full_recipe_path: str):
        """Save the recipe in a json file with a timestamp."""
        # Raise a sepal_ui.warning if there is no loaded models
        if not self.seplan:
            raise SepalWarning(cm.recipe.error.no_seplan)

        data = {
            "signature": "cc19794c0d420e449f36308ce0ede23d03f14be78490d857fbda3289a1910e75",
            "aoi": self.seplan_aoi.export_data(),
            "benefits": self.benefit_model.export_data(),
            "constraints": self.constraint_model.export_data(),
            "costs": self.cost_model.export_data(),
        }

        [
            validation.remove_key(data, key)
            for key in ["updated", "new_changes", "object_set"]
        ]

        save_file(full_recipe_path, data, self.sepal_session)

        self.new_changes = 0

        return full_recipe_path

    def reset(self):
        """Reset the recipe to its default values."""
        # Each of the models will return to its default values and
        # they'll update their respective views by themselves

        self.benefit_model.reset()
        self.constraint_model.reset()
        self.cost_model.reset()

        logger.debug("constraint_model.ids", self.constraint_model.ids)
        self.seplan_aoi.reset()

        self.dash_model.reset()

        self.new_changes = 0

    def get_recipe_path(self, recipe_name: str):
        """generate full recipe path."""

        if self.sepal_session:
            recipe_dir = self.sepal_session.get_remote_dir(
                "module_results/se.plan/recipes"
            )

        else:
            recipe_dir = cp.result_dir / "recipes"
            recipe_dir.mkdir(exist_ok=True)

        recipe_path = Path(recipe_name)

        # add .json if not present
        if recipe_path.suffix != ".json":
            recipe_path = recipe_path.with_suffix(".json")

        # create the json file
        return str(recipe_dir / recipe_path)

    def get_recipe_name(self) -> str:
        """Generate the recipe name based on the aoi name."""
        return str(Path(self.recipe_session_path).stem)

    @observe("new_changes")
    def observe_changes(self, _):
        logger.debug(f"Changes observed in recipe, {self.new_changes} changes")

    @property
    def models(self):
        """Return all models in the recipe."""
        return [
            self.seplan_aoi,
            self.benefit_model,
            self.constraint_model,
            self.cost_model,
        ]
