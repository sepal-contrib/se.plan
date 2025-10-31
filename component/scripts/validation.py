"""functions to read and validate a recipe and return meaningful errors."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from typing import List, Literal, Tuple

from jsonschema import ValidationError, validate

from component.parameter import recipe_schema_path
from component.scripts.file_handler import read_file
from component.types import RecipePaths
import logging
from sepal_ui.scripts.gee_task import GEETask


logger = logging.getLogger("SEPLAN")


@dataclass
class ValidationResult:
    """Result of validating recipe data before loading into models."""

    has_errors: bool = False
    benefits_errors: List[dict] = None
    constraints_errors: List[dict] = None
    costs_errors: List[dict] = None
    raw_data: dict = None  # Store raw data for sanitization
    recipe_path: str = None  # Store recipe path for reference

    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.benefits_errors is None:
            self.benefits_errors = []
        if self.constraints_errors is None:
            self.constraints_errors = []
        if self.costs_errors is None:
            self.costs_errors = []

        # Update has_errors based on actual errors
        self.has_errors = bool(
            self.benefits_errors or self.constraints_errors or self.costs_errors
        )

    @property
    def total_errors(self) -> int:
        """Total number of errors across all data types."""
        return (
            len(self.benefits_errors)
            + len(self.constraints_errors)
            + len(self.costs_errors)
        )


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
        if values[0] not in [0, 1]:
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


def validate_constraint_data(constraints_data: dict) -> Tuple[bool, List[dict]]:
    """
    Validate constraints data before loading into model.

    Checks:
    - All constraint arrays have matching lengths
    - Each constraint has valid values for its data_type

    Args:
        constraints_data: Dictionary containing constraint arrays

    Returns:
        Tuple of (is_valid, list_of_invalid_constraints)
        Each invalid constraint is a dict with keys: index, id, name, data_type, values, error
    """
    invalid_constraints = []

    # Check if constraints data exists and has required keys
    required_keys = [
        "names",
        "ids",
        "values",
        "data_type",
        "themes",
        "assets",
        "descs",
        "units",
    ]

    for key in required_keys:
        if key not in constraints_data:
            logger.error(f"Missing required key in constraints: {key}")
            return False, [{"error": f"Missing required field: {key}", "index": -1}]

    # Check array lengths match
    lengths = {k: len(constraints_data.get(k, [])) for k in required_keys}
    unique_lengths = set(lengths.values())

    if len(unique_lengths) > 1:
        logger.error(f"Constraint arrays have mismatched lengths: {lengths}")
        return False, [{"error": f"Array length mismatch: {lengths}", "index": -1}]

    # Validate each constraint
    num_constraints = len(constraints_data.get("ids", []))

    for i in range(num_constraints):
        try:
            constraint_id = constraints_data["ids"][i]
            name = constraints_data["names"][i]
            data_type = constraints_data["data_type"][i]
            values = constraints_data["values"][i]

            # Validate the values for this constraint
            is_valid, error_msg = validate_constraint_values(values, data_type, name)

            if not is_valid:
                invalid_constraints.append(
                    {
                        "index": i,
                        "id": constraint_id,
                        "name": name,
                        "data_type": data_type,
                        "values": values,
                        "error": error_msg,
                    }
                )
                logger.warning(f"Invalid constraint '{name}' (index {i}): {error_msg}")

        except (IndexError, KeyError) as e:
            logger.error(f"Malformed constraint at index {i}: {e}")
            invalid_constraints.append(
                {
                    "index": i,
                    "id": (
                        constraints_data["ids"][i]
                        if i < len(constraints_data.get("ids", []))
                        else "unknown"
                    ),
                    "name": (
                        constraints_data["names"][i]
                        if i < len(constraints_data.get("names", []))
                        else "unknown"
                    ),
                    "data_type": "unknown",
                    "values": [],
                    "error": f"Malformed data: {str(e)}",
                }
            )

    return len(invalid_constraints) == 0, invalid_constraints


def filter_invalid_constraints(constraints_data: dict) -> Tuple[dict, List[dict]]:
    """
    Filter out invalid constraints from constraints data.

    Args:
        constraints_data: Dictionary containing constraint arrays

    Returns:
        Tuple of (filtered_data, list_of_removed_constraints)
        Each removed constraint contains: index, id, name, data_type, values, error
    """
    is_valid, invalid_constraints = validate_constraint_data(constraints_data)

    # If all valid, return as-is
    if is_valid:
        return constraints_data, []

    # Get indices of invalid constraints
    invalid_indices = set(c["index"] for c in invalid_constraints if c["index"] >= 0)

    # If there's a structural error (index -1), we can't filter safely
    if any(c["index"] == -1 for c in invalid_constraints):
        logger.error("Cannot filter constraints due to structural errors")
        return constraints_data, invalid_constraints

    # Filter out invalid constraints
    filtered_data = {}
    required_keys = [
        "names",
        "ids",
        "values",
        "data_type",
        "themes",
        "assets",
        "descs",
        "units",
    ]

    for key in required_keys:
        filtered_data[key] = [
            constraints_data[key][i]
            for i in range(len(constraints_data[key]))
            if i not in invalid_indices
        ]

    # Preserve other keys that might exist
    for key in constraints_data:
        if key not in required_keys:
            filtered_data[key] = constraints_data[key]

    logger.info(
        f"Filtered out {len(invalid_indices)} invalid constraints from {len(constraints_data['ids'])} total"
    )

    return filtered_data, invalid_constraints


def get_short_traceback(tb_string: str, num_lines: int = 3) -> str:
    """Extract a short traceback snippet from a full traceback string."""
    short_tb = tb_string.splitlines()[-num_lines:]
    return " | ".join([line.strip() for line in short_tb if line.strip()])


def extract_task_error(task: GEETask) -> str:
    """Extract error message from a failed task, checking multiple sources."""

    # Try to get error message from various task attributes
    error_msg = ""
    if getattr(task, "message", None):
        error_msg = str(task.message)
    if not error_msg and getattr(task, "error", None):
        error_msg = str(task.error)

    # Log full traceback if exception is available
    if getattr(task, "exception", None):
        exc = task.exception
        if not error_msg:
            error_msg = str(exc)

    # Check for traceback attribute
    if not error_msg and getattr(task, "traceback", None):
        error_msg = str(task.traceback)

    # Fallback to task state
    if not error_msg:
        error_msg = f"Task failed with state: {task.state}"

    return error_msg


def validate_benefit_data(benefits_data: dict) -> Tuple[bool, List[dict]]:
    """
    Validate benefits data before loading into model.

    Checks:
    - All benefit arrays have matching lengths
    - Each benefit has valid weights (should be numeric 1-7)

    Args:
        benefits_data: Dictionary containing benefit arrays

    Returns:
        Tuple of (is_valid, list_of_invalid_benefits)
        Each invalid benefit is a dict with keys: index, id, name, data_type, values, error
    """
    invalid_benefits = []

    # Check if benefits data exists and has required keys
    required_keys = ["names", "ids", "weights", "themes", "assets", "descs", "units"]

    for key in required_keys:
        if key not in benefits_data:
            logger.error(f"Missing required key in benefits: {key}")
            return False, [{"error": f"Missing required field: {key}", "index": -1}]

    # Check array lengths match
    lengths = {k: len(benefits_data.get(k, [])) for k in required_keys}
    unique_lengths = set(lengths.values())

    if len(unique_lengths) > 1:
        logger.error(f"Benefit arrays have mismatched lengths: {lengths}")
        return False, [{"error": f"Array length mismatch: {lengths}", "index": -1}]

    # Validate each benefit
    num_benefits = len(benefits_data.get("ids", []))

    for i in range(num_benefits):
        try:
            benefit_id = benefits_data["ids"][i]
            name = benefits_data["names"][i]
            weight = benefits_data["weights"][i]

            # Validate the weight (should be numeric 1-7)
            is_valid = True
            error_msg = ""

            if not isinstance(weight, (int, float)):
                is_valid = False
                error_msg = (
                    f"Expected numeric weight (1-7), got {type(weight).__name__}"
                )
            elif weight < 1 or weight > 7:
                is_valid = False
                error_msg = f"Weight must be between 1 and 7, got {weight}"

            if not is_valid:
                invalid_benefits.append(
                    {
                        "index": i,
                        "id": benefit_id,
                        "name": name,
                        "data_type": "numeric (1-7)",
                        "values": weight,
                        "error": error_msg,
                    }
                )
                logger.warning(f"Invalid benefit '{name}' (index {i}): {error_msg}")

        except (IndexError, KeyError) as e:
            logger.error(f"Malformed benefit at index {i}: {e}")
            invalid_benefits.append(
                {
                    "index": i,
                    "id": (
                        benefits_data["ids"][i]
                        if i < len(benefits_data.get("ids", []))
                        else "unknown"
                    ),
                    "name": (
                        benefits_data["names"][i]
                        if i < len(benefits_data.get("names", []))
                        else "unknown"
                    ),
                    "data_type": "numeric (1-7)",
                    "values": None,
                    "error": f"Malformed data: {str(e)}",
                }
            )

    return len(invalid_benefits) == 0, invalid_benefits


def validate_cost_data(costs_data: dict) -> Tuple[bool, List[dict]]:
    """
    Validate costs data before loading into model.

    Costs currently only have metadata (no values to validate).
    This function checks structure validity.

    Args:
        costs_data: Dictionary containing cost arrays

    Returns:
        Tuple of (is_valid, list_of_invalid_costs)
    """
    invalid_costs = []

    # Check if costs data exists and has required keys
    required_keys = ["names", "ids", "assets", "descs", "units"]

    for key in required_keys:
        if key not in costs_data:
            logger.error(f"Missing required key in costs: {key}")
            return False, [{"error": f"Missing required field: {key}", "index": -1}]

    # Check array lengths match
    lengths = {k: len(costs_data.get(k, [])) for k in required_keys}
    unique_lengths = set(lengths.values())

    if len(unique_lengths) > 1:
        logger.error(f"Cost arrays have mismatched lengths: {lengths}")
        return False, [{"error": f"Array length mismatch: {lengths}", "index": -1}]

    # For now, costs don't have values to validate, just structural checks
    # Future: could add validation for asset paths, units format, etc.

    return len(invalid_costs) == 0, invalid_costs


def validate_recipe_data(
    benefits: dict, constraints: dict, costs: dict
) -> ValidationResult:
    """
    Validate all recipe data (benefits, constraints, costs) before loading.

    This is the main validation entry point that should be called before
    importing data into models.

    Args:
        benefits: Benefits data dictionary
        constraints: Constraints data dictionary
        costs: Costs data dictionary

    Returns:
        ValidationResult containing any errors found
    """
    # Validate each data type
    _, benefits_errors = validate_benefit_data(benefits)
    _, constraints_errors = validate_constraint_data(constraints)
    _, costs_errors = validate_cost_data(costs)

    return ValidationResult(
        benefits_errors=benefits_errors,
        constraints_errors=constraints_errors,
        costs_errors=costs_errors,
    )


def sanitize_recipe_data(data: dict, validation_result: ValidationResult) -> dict:
    """
    Sanitize recipe data by clearing invalid values.

    Instead of removing entire layers with bad data, this sets their
    values/weights to empty/default values.

    Args:
        data: Full recipe data dictionary with 'benefits', 'constraints', 'costs'
        validation_result: ValidationResult from validate_recipe_data

    Returns:
        Sanitized copy of the data with invalid values cleared
    """
    import copy

    sanitized = copy.deepcopy(data)

    # Sanitize benefits - set invalid weights to default (4)
    for error in validation_result.benefits_errors:
        idx = error["index"]
        if idx >= 0 and idx < len(sanitized["benefits"].get("weights", [])):
            sanitized["benefits"]["weights"][idx] = 4  # Default weight
            logger.info(
                f"Sanitized benefit '{error['name']}' (index {idx}): set weight to default (4)"
            )

    # Sanitize constraints - set invalid values to []
    for error in validation_result.constraints_errors:
        idx = error["index"]
        if idx >= 0 and idx < len(sanitized["constraints"].get("values", [])):
            sanitized["constraints"]["values"][idx] = []
            logger.info(
                f"Sanitized constraint '{error['name']}' (index {idx}): cleared invalid values"
            )

    # Sanitize costs - currently no values to sanitize
    for error in validation_result.costs_errors:
        idx = error["index"]
        # Future: sanitize cost-specific fields if needed
        logger.info(
            f"Sanitized cost '{error.get('name', 'unknown')}' (index {idx}): no action needed"
        )

    return sanitized
