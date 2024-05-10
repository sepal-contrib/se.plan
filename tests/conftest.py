import pytest
from component.model.recipe import Recipe
from component.widget.alert_state import AlertState
from sepal_ui.scripts import utils as su

su.init_ee()


@pytest.fixture(scope="session")
def empty_recipe() -> Recipe:
    """Create an empty recipe."""

    recipe = Recipe()
    recipe.load_model()

    return recipe


@pytest.fixture(scope="session")
def full_recipe() -> Recipe:
    """Create a loaded recipe."""

    # Load a previously created recipe
    recipe = Recipe()
    recipe.load_model()
    recipe.load("/home/dguerrero/module_results/se.plan/recipes/test_cundinamarca.json")
    # we have to do this manually
    recipe.seplan_aoi.aoi_model.set_object()

    return recipe


@pytest.fixture(scope="session")
def alert():
    return AlertState()
