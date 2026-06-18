"""Regression: a scheduled AOI zoom must use the captured AOI, not the live trait.

During recipe import ``set_object()`` runs several times, and each call starts
with ``clear_output()`` which nulls ``feature_collection`` before rebuilding it.
The zoom is deferred to the GEE thread, so if it re-reads the live trait it can
observe that ``None`` window and raise "You must set the gdf before interacting
with it". The zoom must instead use the AOI snapshot taken when it was scheduled.
"""

from pathlib import Path

import pytest

from component.model.recipe import Recipe
from component.scripts import validation
from component.widget.custom_aoi_view import SeplanAoiView

_RECIPES = Path(__file__).parent / "data/recipes"


def _loaded_model(name: str):
    """Load a real recipe fixture and build its primary AOI feature collection."""
    recipe = Recipe()
    result = recipe.load(_RECIPES / name)
    if isinstance(result, validation.ValidationResult):
        sanitized = validation.sanitize_recipe_data(result.raw_data, result)
        recipe.load_sanitized(sanitized, result.recipe_path)
    model = recipe.seplan_aoi.aoi_model
    model.set_object()
    return model


class _FakeMap:
    """Minimal ``map_`` stand-in that records the zoom call."""

    def __init__(self):
        self.zoomed = None

    def remove_layer(self, name, none_ok=False):
        pass

    def zoom_bounds(self, bounds):
        self.zoomed = bounds

    async def add_ee_layer_async(self, fc, vis, name):
        pass


class _StubView:
    """Stand-in for SeplanAoiView holding only what ``_zoom_async`` touches."""

    aoi_dc = None

    def __init__(self, model, map_):
        self.model = model
        self.map_ = map_
        self.updated = 0


@pytest.mark.asyncio
@pytest.mark.parametrize("recipe_name", ["test_recipe.json", "antioquia_1.json"])
async def test_total_bounds_async_uses_snapshot_over_live_trait(recipe_name):
    """total_bounds_async must compute from a passed AOI, not the live trait."""
    model = _loaded_model(recipe_name)
    fc = model.feature_collection
    assert fc is not None

    # clear_output() inside a concurrent set_object() nulls the live trait
    model.feature_collection = None

    bounds = await model.total_bounds_async(fc)

    assert len(bounds) == 4
    assert bounds[0] < bounds[2] and bounds[1] < bounds[3]


@pytest.mark.asyncio
async def test_zoom_async_uses_snapshot_when_feature_collection_cleared():
    """_zoom_async must zoom to the captured AOI even when the live trait is None."""
    model = _loaded_model("test_recipe.json")
    fc = model.feature_collection
    assert fc is not None

    model.feature_collection = None  # the clear_output() window

    fake_map = _FakeMap()
    await SeplanAoiView._zoom_async(_StubView(model, fake_map), fc)

    assert fake_map.zoomed is not None
    assert len(fake_map.zoomed) == 4
