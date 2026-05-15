import os
from pathlib import Path
import pytest
from component.model.recipe import Recipe
from component.scripts import validation
from component.widget.alert_state import AlertState
from sepal_ui.scripts import utils as su

if os.getenv("EARTHENGINE_TOKEN") or (Path.home() / ".config" / "earthengine" / "credentials").exists():
    su.init_ee()
test_recipe_path = Path(__file__).parent / "data/recipes/test_recipe.json"


def load_recipe(recipe: Recipe, path: Path) -> Recipe:
    """Load a recipe fixture, sanitizing stale invalid values when needed."""
    result = recipe.load(path)

    if isinstance(result, validation.ValidationResult):
        sanitized = validation.sanitize_recipe_data(result.raw_data, result)
        recipe.load_sanitized(sanitized, result.recipe_path)

    return recipe


@pytest.fixture(scope="session")
def empty_recipe() -> Recipe:
    """Create an empty recipe."""

    return Recipe()


@pytest.fixture(scope="session")
def full_recipe() -> Recipe:
    """Create a loaded recipe."""

    # Load a previously created recipe
    recipe = Recipe()
    load_recipe(recipe, test_recipe_path)
    recipe.seplan_aoi.aoi_model.set_object()

    return recipe


@pytest.fixture(scope="session")
def alert():
    return AlertState()
