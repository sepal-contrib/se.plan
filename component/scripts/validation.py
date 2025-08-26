"""functions to read and validate a recipe and return meaningful errors."""

import json
from pathlib import Path
from typing import Optional
from typing import List, Literal, Tuple

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

    logger.debug(f"are_comparable called with recipe_paths: {recipe_paths}")
    aoi_values = set()

    for recipe_id, recipe_info in recipe_paths.items():
        logger.debug(f"Processing recipe {recipe_id}: {recipe_info}")
        data = read_file(recipe_info["path"], sepal_session=sepal_session)
        logger.debug(f"Raw data for recipe {recipe_id}: {data}")

        remove_key(data, "updated")
        remove_key(data, "new_changes")
        remove_key(data, "object_set")

        logger.debug(f"Data after removing keys for recipe {recipe_id}: {data}")

        primary_aoi = data["aoi"]["primary"]
        logger.debug(f"Primary AOI for recipe {recipe_id}: {primary_aoi}")

        aoi_json = json.dumps(primary_aoi, sort_keys=True)
        logger.debug(f"AOI JSON for recipe {recipe_id}: {aoi_json}")

        aoi_values.add(aoi_json)
        logger.debug(f"Current AOI values set: {aoi_values}")

    logger.debug(f"Final AOI values set (length: {len(aoi_values)}): {aoi_values}")

    # Raise an error if the recipes are not comparable
    if len(aoi_values) > 1:
        logger.error(
            f"Recipes are not comparable. Found {len(aoi_values)} different AOIs: {aoi_values}"
        )
        raise Exception(
            "Error: The recipes are not comparable. All recipes must have the same main Area of Interest."
        )

    return True


def read_recipe_data(recipe_path: str, sepal_session=None):
    """Read the recipe data from the recipe file."""

    recipe_path = Path(validate_recipe(recipe_path, sepal_session=sepal_session))

    data = read_file(recipe_path, sepal_session=sepal_session)

    # Remove all the "updated" keys from the data in the second level
    [remove_key(data, key) for key in ["updated", "new_changes", "object_set"]]

    return recipe_path, data


def validate_constraint_values(
    values: list,
    data_type: Literal["binary", "categorical", "continuous"],
    layer_name: str = "constraint",
) -> Tuple[bool, str]:
    """
    Validate constraint values based on data type.

    Args:
        values: List of constraint values to validate
        data_type: Type of constraint data (binary, categorical, continuous)
        layer_name: Name of the layer for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not values or len(values) == 0:
        if data_type == "categorical":
            return False, f"Please select at least one category to exclude"
        elif data_type == "binary":
            return False, f"Please select a value (0 or 1)"
        else:
            return False, f"Please configure constraint values"

    if data_type == "binary":
        if len(values) != 1:
            return False, f"Please select exactly one value (0 or 1)"
        if values[0] is None:
            return False, f"Please select a valid value (0 or 1)"

    elif data_type == "categorical":
        if any(val is None for val in values):
            return False, f"Please select valid categories to exclude"
        if len(values) == 0:
            return False, f"Please select at least one category to exclude"

    elif data_type == "continuous":
        if len(values) != 2:
            return False, f"Please set a valid range (min and max values)"
        if any(val is None for val in values):
            return False, f"Please set valid min and max values"
        min_val, max_val = values
        if min_val >= max_val:
            return (
                False,
                f"Min value ({min_val}) must be less than max value ({max_val})",
            )

    else:
        return (
            False,
            f"Unknown data type '{data_type}'. Supported types: binary, categorical, continuous.",
        )

    return True, ""


def validate_mask_image_parameters(
    asset_id: str,
    data_type: Literal["binary", "categorical", "continuous"],
    maskout_values: list,
) -> None:
    """
    Validate parameters for mask_image function.

    Args:
        asset_id: ID of the asset to mask
        data_type: Type of constraint data
        maskout_values: Values to use for masking

    Raises:
        ValueError: If validation fails with descriptive error message
    """
    # Check for empty or None values
    if not maskout_values or len(maskout_values) == 0:
        raise ValueError(
            f"No values provided for constraint layer, please select at least one value to exclude."
        )

    # Data type specific validation
    if data_type == "binary":
        if len(maskout_values) != 1:
            raise ValueError(
                f"Binary constraint layer requires exactly 1 value, got {len(maskout_values)} values."
            )
        if maskout_values[0] is None:
            raise ValueError(
                f"Binary constraint layer has invalid value, please select a valid value."
            )

    elif data_type == "categorical":
        if any(val is None for val in maskout_values):
            raise ValueError(
                f"Categorical constraint layer contains invalid values, please select valid categories."
            )
        if len(maskout_values) == 0:
            raise ValueError(
                f"Categorical constraint layer requires at least 1 category to be selected."
            )

    elif data_type == "continuous":
        if len(maskout_values) != 2:
            raise ValueError(
                f"Continuous constraint layer requires exactly 2 values (min, max), got {len(maskout_values)} values."
            )
        if any(val is None for val in maskout_values):
            raise ValueError(
                f"Continuous constraint layer has invalid range values, please set valid min/max values."
            )
        min_val, max_val = maskout_values
        if min_val >= max_val:
            raise ValueError(
                f"Continuous constraint layer has invalid range: min ({min_val}) must be less than max ({max_val})."
            )

    else:
        raise ValueError(
            f"Unknown data type '{data_type}' for constraint layer. Supported types: binary, categorical, continuous."
        )


def validate_constraint_model_data(
    names: List[str],
    ids: List[str],
    values: List[list],
    data_types: List[str],
) -> Tuple[bool, List[str]]:
    """
    Validate all constraints in a constraint model for use in calculations.

    Args:
        names: List of constraint layer names
        ids: List of constraint layer IDs
        values: List of constraint values
        data_types: List of constraint data types

    Returns:
        Tuple of (all_valid, list_of_error_messages)
    """
    errors = []

    for i, layer_id in enumerate(ids):
        layer_name = names[i] if i < len(names) else layer_id
        layer_values = values[i] if i < len(values) else []
        data_type = data_types[i] if i < len(data_types) else "unknown"

        # Use the constraint values validation
        is_valid, error_msg = validate_constraint_values(
            layer_values, data_type, layer_name
        )
        if not is_valid:
            # Add layer name context for model-level validation
            errors.append(f"'{layer_name}': {error_msg}")

    return len(errors) == 0, errors
