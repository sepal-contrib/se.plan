"""functions to read and validate a recipe and return meaningful errors."""
import json
from pathlib import Path
from typing import Optional

from jsonschema import ValidationError, validate
from sepal_ui.sepalwidgets import TextField

from component.parameter import recipe_schema_path


def find_missing_property(instance, schema):
    required_properties = schema.get("required", [])
    for prop in required_properties:
        if prop not in instance:
            return prop
    return None


def validate_recipe(
    recipe_path: str, text_field_msg: Optional[TextField] = None
) -> Optional[Path]:
    """Read user file and performs all validation and corresponding checks."""
    try:
        # open the file and load the models
        with Path(recipe_path).open() as f:
            data = json.loads(f.read())

    except FileNotFoundError:
        error_msg = "The file could not be found. Please check that the file exists"
        not text_field_msg or setattr(text_field_msg, "error_messages", error_msg)
        raise FileNotFoundError(error_msg)

    except json.decoder.JSONDecodeError:
        error_msg = "The file is not a valid json file. Please check that the file is a valid json file"
        not text_field_msg or setattr(text_field_msg, "error_messages", error_msg)
        raise json.decoder.JSONDecodeError(error_msg)

    # Load the JSON schema
    with open(recipe_schema_path, "r") as f:
        schema = json.load(f)

    try:
        # use the jsonschema library to validate the recipe schema
        validate(instance=data, schema=schema)

    except ValidationError as e:
        # Constructing a path string
        print(e)
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

        not text_field_msg or setattr(text_field_msg, "error_messages", error_msg)

        raise ValidationError(e)

    return recipe_path
