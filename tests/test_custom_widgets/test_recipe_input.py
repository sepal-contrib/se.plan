import pytest

from jsonschema import ValidationError

from component.widget.custom_widgets import RecipeInput
from tests.data.test_recipes import test_error_recipe_path, test_recipe_path


def test_init_recipe_input():
    """Test the initialization of the RecipeInput widget."""

    recipe_input = RecipeInput()

    assert not recipe_input.load_recipe_path
    assert not recipe_input.valid


def test_invalid_recipe():
    """Test the validation of an invalid recipe."""

    recipe_input = RecipeInput()

    with pytest.raises(ValidationError):
        recipe_input.validate_input({"new": str(test_error_recipe_path)})

    # The error is surfaced on the file input
    assert recipe_input.file_input.error_messages

    # and the recipe is not accepted
    assert recipe_input.valid is False
    assert recipe_input.load_recipe_path is None


def test_valid_recipe():
    """Test the validation of a valid recipe."""

    recipe_input = RecipeInput()
    recipe_input.validate_input({"new": str(test_recipe_path)})

    # No error is surfaced
    assert not recipe_input.file_input.error_messages

    # and the recipe is accepted
    assert recipe_input.valid
    assert recipe_input.load_recipe_path == str(test_recipe_path)


def test_valid_and_invalid_recipe():
    """Test loading a valid recipe followed by an invalid one."""

    recipe_input = RecipeInput()
    recipe_input.validate_input({"new": str(test_recipe_path)})

    # Now we load an invalid recipe
    with pytest.raises(ValidationError):
        recipe_input.validate_input({"new": str(test_error_recipe_path)})

    # The error is surfaced on the file input
    assert recipe_input.file_input.error_messages

    # and the previously valid state is cleared
    assert recipe_input.valid is False
    assert recipe_input.load_recipe_path is None
