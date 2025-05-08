"""functions to read and validate a recipe and return meaningful errors."""

import json
from pathlib import Path
from typing import Optional

from jsonschema import ValidationError, validate

from component.parameter import recipe_schema_path
from component.scripts.file_handler import read_file
from component.types import RecipePaths
import logging

logger = logging.getLogger("SEPLAN")


def find_missing_property(instance, schema):
    required_properties = schema.get("required", [])
    for prop in required_properties:
        if prop not in instance:
            return prop
    return None


def validate_recipe(
    recipe_path: str, file_input=None, sepal_session=None
) -> Optional[Path]:
    """Read user file and performs all validation and corresponding checks."""
    logger.debug(f"Validating recipe: {recipe_path}+++{sepal_session}")
    try:
        data = read_file(recipe_path, sepal_session=sepal_session)
    except FileNotFoundError:
        error_msg = "The file could not be found. Please check that the file exists"
        not file_input or setattr(file_input, "error_messages", [error_msg])
        raise FileNotFoundError(f"{error_msg}")

    except json.decoder.JSONDecodeError:
        error_msg = "The file is not a valid json file. Please check that the file is a valid json file"
        not file_input or setattr(file_input, "error_messages", [error_msg])
        raise json.decoder.JSONDecodeError(error_msg)

    # Load the JSON schema
    with open(recipe_schema_path, "r") as f:
        schema = json.load(f)

    try:
        # use the jsonschema library to validate the recipe schema
        validate(instance=data, schema=schema)

    except ValidationError as e:
        # Constructing a path string
        logger.debug(e)
        path = ".".join(map(str, e.path))

        # Check if the error is related to the signature field
        if e.validator == "required":
            # Get the path of the error
            path_list = list(e.path)
            # Navigate to the location of the error in the schema
            error_schema = schema
            for p in path_list:
                error_schema = error_schema["properties"][p]
            # Navigate to the location of the error in the instance data
            error_instance = data
            for p in path_list:
                error_instance = error_instance[p]
            # Find the missing property
            missing_property = find_missing_property(error_instance, error_schema)
            error_msg = f"Error: Missing required field '{missing_property}' in {path if path else 'root'}"

        elif path == "signature":
            error_msg = (
                "Error: The signature is invalid, check the file is a valid recipe."
            )

        else:
            # Creating a detailed error error_msg for other fields
            error_msg = f"Error in field '{path}': {e.message}"

        not file_input or setattr(file_input, "error_messages", [error_msg])

        raise ValidationError(e)

    return recipe_path


def remove_key(data, key_to_remove):
    """Remove a key from a dictionary."""
    if isinstance(data, dict):
        if key_to_remove in data:
            del data[key_to_remove]
        for key, value in list(data.items()):
            remove_key(value, key_to_remove)
    elif isinstance(data, list):
        for item in data:
            remove_key(item, key_to_remove)


def validate_scenarios_recipes(recipe_paths: RecipePaths):
    """Validate all the recipes in the scenario."""

    for recipe_id, recipe_info in recipe_paths.items():
        if not recipe_info["valid"]:
            raise Exception(f"Error: Recipe '{recipe_id}' is not a valid recipe.")

    # Validate that all the pahts have an unique stem name

    recipe_stems = [
        Path(recipe_info["path"]).stem for recipe_info in recipe_paths.values()
    ]

    logger.debug(f"Validating recipies {recipe_stems}")

    if len(recipe_stems) != len(set(recipe_stems)):
        raise Exception(
            "Error: To compare recipes, all the recipes must have an unique name."
        )

    return True


def are_comparable(recipe_paths: RecipePaths, sepal_session=None):
    """Check if the recipes are comparable based on their primary AOI (Area of Interest)."""

    aoi_values = set()

    for _, recipe_info in recipe_paths.items():
        data = read_file(recipe_info["path"], sepal_session=sepal_session)
        remove_key(data, "updated")
        remove_key(data, "new_changes")
        primary_aoi = data["aoi"]["primary"]
        aoi_values.add(json.dumps(primary_aoi, sort_keys=True))

    # Raise an error if the recipes are not comparable
    if len(aoi_values) > 1:
        raise Exception(
            "Error: The recipes are not comparable. All recipes must have the same main Area of Interest."
        )

    return True


def read_recipe_data(recipe_path: str, sepal_session=None):
    """Read the recipe data from the recipe file."""

    recipe_path = Path(validate_recipe(recipe_path, sepal_session=sepal_session))

    data = read_file(recipe_path, sepal_session=sepal_session)

    # Remove all the "updated" keys from the data in the second level
    [remove_key(data, key) for key in ["updated", "new_changes"]]

    return recipe_path, data
