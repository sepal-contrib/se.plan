"""Regression tests for recipe session-path source-of-truth.

The right-panel header (RecipeHeader) reads ``recipe.recipe_session_path``
directly, while RecipeView keeps a one-way mirror copy. These tests guard
against the drift where the tile's new/save flows updated only the mirror,
leaving the model (and therefore the header, exports and asset naming) stale.
"""

from component.model.recipe import RECIPE_SIGNATURE, Recipe
from component.tile.recipe_tile import RecipeView
from component.widget.alert_state import Alert
from component.widget.recipe_header import RecipeHeader


def test_save_updates_model_session_path(tmp_path):
    """Recipe.save makes the saved path the canonical session path."""
    recipe = Recipe()
    target = tmp_path / "saved_recipe.json"

    recipe.save(str(target))

    assert recipe.recipe_session_path == str(target)


def test_new_event_writes_model_not_just_view():
    """Creating a new recipe via the tile must update the model trait.

    Previously ``new_event`` set only ``RecipeView.recipe_session_path`` (the
    mirror), so the header kept showing the old name.
    """
    recipe = Recipe()
    view = RecipeView(recipe=recipe)

    view.card_new.recipe_name = "my_new_recipe"
    # new_event is a loading_button-wrapped handler, invoked like an ipyvuetify
    # event callback: (widget, event, data).
    view.new_event(None, None, None)

    expected = recipe.get_recipe_path("my_new_recipe")
    # the model (source of truth) is updated, not just the view's copy
    assert recipe.recipe_session_path == expected
    # and the view's mirror reflects it via the one-way link
    assert view.recipe_session_path == expected


def test_save_event_writes_model(tmp_path):
    """Saving via the tile keeps the model path in sync with the written file."""
    recipe = Recipe()
    view = RecipeView(recipe=recipe)

    # seed a session path so save_event renames within its folder
    recipe.recipe_session_path = str(tmp_path / "old_name.json")
    view.card_save.recipe_name = "new_name"

    view.save_event(None, None, None)

    expected = str(tmp_path / "new_name.json")
    assert recipe.recipe_session_path == expected
    assert view.recipe_session_path == expected


def test_view_trait_mirrors_model():
    """The view's recipe_session_path is a pure mirror of the model trait."""
    recipe = Recipe()
    view = RecipeView(recipe=recipe)

    recipe.recipe_session_path = "/tmp/some/path.json"

    assert view.recipe_session_path == "/tmp/some/path.json"


def test_to_dict_is_single_source_of_truth():
    """to_dict carries the real signature and the canonical recipe shape."""
    recipe = Recipe()
    data = recipe.to_dict()

    assert data["signature"] == RECIPE_SIGNATURE
    assert set(data) == {"signature", "aoi", "benefits", "constraints", "costs"}


def test_header_inspector_uses_real_signature():
    """The header preview reuses Recipe.to_dict (no 'live-session' sentinel)."""
    recipe = Recipe()
    header = RecipeHeader(recipe=recipe, alert=Alert())

    header._on_view()

    assert header.inspector.data_dict["signature"] == RECIPE_SIGNATURE
