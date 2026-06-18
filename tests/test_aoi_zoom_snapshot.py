"""Regression: a scheduled AOI zoom must use the captured AOI, not the live trait.

During recipe import ``set_object()`` runs several times, and each call starts
with ``clear_output()`` which nulls ``feature_collection`` before rebuilding it.
The zoom is deferred to the GEE thread, so if it re-reads the live trait it can
observe that ``None`` window and raise "You must set the gdf before interacting
with it". The zoom must instead use the AOI snapshot taken when it was scheduled.
"""

import types
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


class _FakeBtn:
    """Records the loading/disabled state pysepal's loading button toggles."""

    def __init__(self):
        self.loading = False
        self.disabled = False


class _StubView:
    """Stand-in for SeplanAoiView holding only what ``_zoom_async`` touches."""

    aoi_dc = None

    def __init__(self, model, map_):
        self.model = model
        self.map_ = map_
        self.updated = 0
        self.btn = _FakeBtn()


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


@pytest.mark.asyncio
async def test_update_aoi_holds_button_loading_until_zoom_completes():
    """The validate button stays loading from schedule until the async zoom ends."""
    captured = {}

    class _Gee:
        def create_task(self, func, key=None, on_error=None):
            captured["func"] = func
            return types.SimpleNamespace(start=lambda: None)

    sentinel_fc = object()

    class _Model:
        gee_interface = _Gee()
        feature_collection = sentinel_fc

        def set_object(self):
            pass

        async def total_bounds_async(self, fc):
            assert fc is sentinel_fc
            return [0.0, 0.0, 1.0, 1.0]

    view = SeplanAoiView.__new__(SeplanAoiView)  # skip the UI-heavy __init__
    view.gee = True
    view.map_ = _FakeMap()
    view.model = _Model()
    view.alert = types.SimpleNamespace(add_msg=lambda *a, **k: None)
    view.btn = _FakeBtn()
    view.aoi_dc = None
    view.updated = 0
    view._app_model = None

    view._update_aoi()
    # spinner shown while the background task is still pending
    assert view.btn.loading is True
    assert view.btn.disabled is True

    await captured["func"]()  # run the deferred _zoom_async(fc)
    # cleared once the AOI is actually loaded
    assert view.btn.loading is False
    assert view.btn.disabled is False
    assert view.map_.zoomed == [0.0, 0.0, 1.0, 1.0]
