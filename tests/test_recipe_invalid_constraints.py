"""Test recipe loading with invalid constraints."""

from pathlib import Path

from component.model.recipe import Recipe
from component.scripts.validation import ValidationResult, filter_invalid_constraints


bad_recipe_path = Path(__file__).parent / "data/recipes/bad_recipe.json"
good_recipe_path = Path(__file__).parent / "data/recipes/test_recipe.json"


def test_load_recipe_with_invalid_constraints_returns_validation_result():
    """Loading a recipe with invalid constraints returns a ValidationResult."""
    recipe = Recipe()
    result = recipe.load(str(bad_recipe_path))

    assert isinstance(result, ValidationResult)
    assert result.has_errors
    assert result.total_errors > 0
    assert len(result.constraints_errors) > 0
    assert result.raw_data is not None
    assert result.recipe_path == str(bad_recipe_path)


def test_invalid_constraint_details():
    """The validation result identifies the specific invalid constraint."""
    recipe = Recipe()
    result = recipe.load(str(bad_recipe_path))

    freshwater = next(
        (c for c in result.constraints_errors if c["id"] == "custom_constraint_0"),
        None,
    )

    assert freshwater is not None
    assert freshwater["name"] == "Freshwater"
    assert freshwater["data_type"] == "binary"
    assert freshwater["values"] == [50, 40, 80]
    assert "0 or 1" in freshwater["error"]


def test_filter_removes_invalid_and_keeps_valid():
    """filter_invalid_constraints strips the bad entry and preserves the rest."""
    recipe = Recipe()
    result = recipe.load(str(bad_recipe_path))

    filtered, removed = filter_invalid_constraints(result.raw_data["constraints"])

    assert len(removed) > 0
    assert "custom_constraint_0" not in filtered["ids"]  # Freshwater gone
    assert "treecover_with_potential" in filtered["ids"]
    assert "custom_constraint_2" in filtered["ids"]  # Mangrove
    assert "custom_constraint_1" in filtered["ids"]  # Land Cover
    assert len(filtered["ids"]) == 3


def test_load_sanitized_imports_only_valid_constraints():
    """load_sanitized loads the recipe with invalid constraints stripped."""
    recipe = Recipe()
    result = recipe.load(str(bad_recipe_path))

    filtered, _ = filter_invalid_constraints(result.raw_data["constraints"])
    sanitized_data = result.raw_data.copy()
    sanitized_data["constraints"] = filtered

    recipe.load_sanitized(sanitized_data, result.recipe_path)

    assert recipe.recipe_session_path == str(bad_recipe_path)
    assert "custom_constraint_0" not in recipe.constraint_model.ids
    assert "treecover_with_potential" in recipe.constraint_model.ids
    assert len(recipe.constraint_model.ids) == 3


def test_load_valid_recipe_has_no_constraint_errors():
    """A recipe with valid constraints has no constraint errors even if other errors exist."""
    recipe = Recipe()
    result = recipe.load(str(good_recipe_path))

    # test_recipe.json has benefit weight issues but no constraint errors
    if isinstance(result, ValidationResult):
        assert len(result.constraints_errors) == 0
    else:
        # If no errors at all, the recipe loaded directly
        assert isinstance(result, Recipe)
