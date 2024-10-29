import sys
from pathlib import Path

sys.path = [str(Path(".").resolve())] + sys.path

print(sys.path)

import pytest
from component.types import RecipePaths
from tests.data.test_recipes import (
    test_recipe_path,
    test_antq1_recipe_path,
    test_antq2_recipe_path,
)
from component.scripts.validation import are_comparable, validate_scenarios_recipes


test_recipe_path, test_antq1_recipe_path, test_antq2_recipe_path


def test_validate_scenarios_recipes():

    recipe_paths: RecipePaths = {
        "recipe1": {"path": test_antq1_recipe_path, "valid": True},
        "recipe2": {"path": test_antq2_recipe_path, "valid": True},
    }

    assert validate_scenarios_recipes(recipe_paths)

    # Compare recipes with the same name, should trigger an exception
    recipe_paths: RecipePaths = {
        "recipe1": {"path": test_antq1_recipe_path, "valid": True},
        "recipe2": {"path": test_antq1_recipe_path, "valid": True},
    }

    with pytest.raises(Exception):
        validate_scenarios_recipes(recipe_paths)


def test_are_comparable():

    recipe_paths: RecipePaths = {
        "recipe1": {"path": test_antq1_recipe_path, "valid": True},
        "recipe2": {"path": test_antq2_recipe_path, "valid": True},
    }

    assert are_comparable(recipe_paths)

    # Validate recipes with different AOI, should trigger an exception
    recipe_paths: RecipePaths = {
        "recipe1": {"path": test_antq1_recipe_path, "valid": True},
        "recipe2": {"path": test_recipe_path, "valid": True},
    }

    with pytest.raises(Exception):
        are_comparable(recipe_paths)


if __name__ == "__main__":
    # Run pytest with the current file
    pytest.main([__file__, "-s", "-vv"])
