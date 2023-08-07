"""functions to read and validate a recipe and return meaningful errors."""
import json
from pathlib import Path
from typing import Optional

from jsonschema import ValidationError, validate
from sepal_ui.sepalwidgets import TextField

from component.parameter import recipe_schema_path


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
        path = ".".join(map(str, e.path))

        # Check if the error is related to the signature field
        if path == "signature":
            error_msg = "Error: The signature is invalid."
        else:
            # Creating a detailed error error_msg for other fields
            error_msg = f"Error in field '{path}': {e.message}"

        not text_field_msg or setattr(text_field_msg, "error_messages", error_msg)

        raise ValidationError(e)

    return recipe_path
