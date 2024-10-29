from pathlib import Path
import pytest
from component.model.recipe import Recipe
from component.widget.alert_state import AlertState
from sepal_ui.scripts import utils as su

su.init_ee()
test_recipe_path = Path(__file__).parent / "data/recipes/test_recipe.json"


@pytest.fixture(scope="session")
def empty_recipe() -> Recipe:
    """Create an empty recipe."""

    return Recipe()


@pytest.fixture(scope="session")
def full_recipe() -> Recipe:
    """Create a loaded recipe."""

    # Load a previously created recipe
    recipe = Recipe()
    recipe.load(test_recipe_path)
    recipe.seplan_aoi.aoi_model.set_object()

    return recipe


@pytest.fixture(scope="session")
def alert():
    return AlertState()
