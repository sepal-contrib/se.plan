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
        recipe_input.select_file(test_error_recipe_path)

    # Check this is not empty
    assert recipe_input.text_field_msg.error_messages

    # Check value is not valid
    assert recipe_input.valid is False
    assert recipe_input.load_recipe_path is None


def test_valid_recipe():
    """Test the validation of an invalid recipe."""

    recipe_input = RecipeInput()
    recipe_input.select_file(str(test_recipe_path))

    # Check this is not empty
    assert not recipe_input.text_field_msg.error_messages

    # Check value is not valid
    assert recipe_input.valid
    assert recipe_input.load_recipe_path == str(test_recipe_path)


def test_valid_and_invalid_recipe():
    """Test the validation of an invalid recipe."""

    recipe_input = RecipeInput()
    recipe_input.select_file(str(test_recipe_path))

    # Now we load an invalid recipe
    with pytest.raises(ValidationError):
        recipe_input.select_file(test_error_recipe_path)

    # Check this is not empty
    assert recipe_input.text_field_msg.error_messages

    # Check value is not valid
    assert recipe_input.valid is False
    assert recipe_input.load_recipe_path is None
