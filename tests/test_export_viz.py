"""Tests for the export visualization parameters (matching the on-map styling)."""

import asyncio

import ee

from component import parameter as cp
from component.scripts.gee import apply_export_viz, get_export_viz_params


class _StubGee:
    """Minimal gee_interface stand-in: resolves ee objects via ``get_info_async``."""

    async def get_info_async(self, ee_object):
        return ee_object.getInfo()


def test_index_uses_layer_vis():
    params = get_export_viz_params("index", "constraint_index")

    assert params["name"] == "default"
    assert params["type"] == "continuous"
    assert params["min"] == cp.layer_vis["min"]
    assert params["max"] == cp.layer_vis["max"]
    assert params["palette"] == cp.layer_vis["palette"]


def test_constraint_is_binary_categorical():
    binary = cp.map_vis["binary"]
    params = get_export_viz_params("constraint", "any")

    assert params["type"] == "categorical"
    assert params["values"] == [0, 1]
    assert params["labels"] == binary["names"]
    assert params["min"] == binary["min"]
    assert params["max"] == binary["max"]
    assert params["palette"] == binary["palette"]


def test_benefit_uses_provided_min_max_with_gradient_palette():
    params = get_export_viz_params("benefit", "any", min_max=(1.0, 4.5))

    assert params["palette"] == cp.map_vis["gradient"]["palette"]
    assert params["min"] == 1.0
    assert params["max"] == 4.5


def test_cost_falls_back_to_gradient_defaults_without_min_max():
    gradient = cp.map_vis["gradient"]
    params = get_export_viz_params("cost", "any")

    assert params["min"] == gradient["min"]
    assert params["max"] == gradient["max"]
    assert params["palette"] == gradient["palette"]


def test_unknown_theme_returns_empty():
    assert get_export_viz_params("mystery", "any") == {}


def test_bands_included_when_provided():
    params = get_export_viz_params("index", "any", bands=["constant"])
    assert params["bands"] == ["constant"]


def test_bands_absent_when_not_provided():
    assert "bands" not in get_export_viz_params("index", "any")


def test_apply_export_viz_is_noop_for_unknown_theme():
    sentinel = object()
    # unknown theme -> image returned unchanged, no GEE calls made
    result = asyncio.run(apply_export_viz(sentinel, "mystery", "any", None, None))
    assert result is sentinel


def test_apply_export_viz_embeds_full_index_properties():
    # ee.Image.constant(3) has a single band named "constant"
    styled = asyncio.run(
        apply_export_viz(
            ee.Image.constant(3), "index", "constraint_index", None, _StubGee()
        )
    )
    props = styled.toDictionary().getInfo()

    assert props["visualization_0_name"] == "default"
    assert props["visualization_0_type"] == "continuous"
    assert props["visualization_0_bands"] == "constant"
    assert props["visualization_0_min"] == "0"
    assert props["visualization_0_max"] == "5"
    assert props["visualization_0_palette"] == ",".join(cp.layer_vis["palette"])


def test_apply_export_viz_benefit_embeds_gradient_and_bands():
    aoi = ee.FeatureCollection(ee.Geometry.Rectangle([0, 0, 1, 1]))
    styled = asyncio.run(
        apply_export_viz(ee.Image.constant(3), "benefit", "any", aoi, _StubGee())
    )
    props = styled.toDictionary().getInfo()

    gradient_palette = ",".join(cp.map_vis["gradient"]["palette"])
    assert props["visualization_0_palette"] == gradient_palette
    assert props["visualization_0_bands"] == "constant"
    # data-driven stretch: a constant image has min == max
    assert props["visualization_0_min"] == props["visualization_0_max"]
