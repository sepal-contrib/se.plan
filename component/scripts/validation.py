"""functions to read and validate a recipe and return meaningful errors."""
import json
from pathlib import Path


def validate_recipe(file_: Path, text_field_msg: str):
    """Read user file and performs all validation and corresponding checks."""
    # Check there's the right number of models inside the file
    # Check the models have all the right parameters
    try:
        # open the file and load the models
        with file_.open() as f:
            data = json.loads(f.read())

    except Exception:
        error_msg = "The file could not be read. Please check that the file is a valid json file"
        text_field_msg.error_messages = error_msg
        raise ValueError(error_msg)

    # Check the data starts with the recipe hash and raise an error if not
    if data["recipe_hash"] != "recipe_hash":
        error_msg = "The recipe hash is not valid"
        text_field_msg.error_messages = error_msg
        raise ValueError(error_msg)

    return file_
