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
from component.scripts.validation import (
    are_comparable,
    validate_benefit_data,
    validate_scenarios_recipes,
)


test_recipe_path, test_antq1_recipe_path, test_antq2_recipe_path


def _benefits(weights):
    """Build a minimal, length-consistent benefits dict for the given weights."""
    n = len(weights)
    return {
        "names": [f"benefit_{i}" for i in range(n)],
        "ids": [f"id_{i}" for i in range(n)],
        "weights": weights,
        "themes": ["bii"] * n,
        "assets": ["asset"] * n,
        "descs": ["desc"] * n,
        "units": ["unit"] * n,
    }


def test_benefit_weight_zero_is_valid():
    """Weight 0 means 'benefit disabled' and must pass validation.

    The weight selector (component/widget/benefit_row.py) only offers
    values 0-4, so 0 is a legitimate, app-produced value.
    """
    is_valid, errors = validate_benefit_data(_benefits([0, 4, 0, 0]))

    assert is_valid
    assert errors == []


def test_benefit_full_weight_range_is_valid():
    """All selectable weights (0-4) are accepted."""
    is_valid, errors = validate_benefit_data(_benefits([0, 1, 2, 3, 4]))

    assert is_valid
    assert errors == []


def test_benefit_weight_above_range_is_invalid():
    """Weights above the selectable range (>4) are rejected."""
    is_valid, errors = validate_benefit_data(_benefits([5]))

    assert not is_valid
    assert len(errors) == 1
    assert errors[0]["values"] == 5


def test_benefit_weight_below_range_is_invalid():
    """Negative weights are rejected."""
    is_valid, errors = validate_benefit_data(_benefits([-1]))

    assert not is_valid
    assert len(errors) == 1


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
