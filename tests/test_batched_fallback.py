"""Test the batched fallback mechanism for statistics computation."""

import asyncio
from unittest.mock import Mock, AsyncMock, patch

import ee
import pytest


def _img():
    """A real, constructable ee.Image standing in for a layer.

    The statistics code builds lazy ee graphs from these inputs; only
    ``get_info_async`` (mocked in these tests) actually reaches GEE, so the
    inputs just need to be valid ee objects, not Mocks.
    """
    return ee.Image(1)


def _fc():
    """A real, constructable ee.FeatureCollection standing in for an AOI."""
    return ee.FeatureCollection([ee.Feature(ee.Geometry.Point([0, 0]))])


def create_mock_recipe():
    """Create a mock recipe with AOI features."""
    mock_recipe = Mock()
    mock_recipe.recipe_session_path = "/tmp/test_recipe"
    mock_recipe.get_recipe_name.return_value = "test_recipe"

    mock_seplan = Mock()
    mock_recipe.seplan = mock_seplan

    mock_aoi_model = Mock()
    mock_seplan.aoi_model = mock_aoi_model

    main_features = {"Main AOI": {"ee_feature": _fc(), "color": "#FF0000"}}
    secondary_features = {
        "Sub AOI 1": {"ee_feature": _fc(), "color": "#00FF00"},
        "Sub AOI 2": {"ee_feature": _fc(), "color": "#0000FF"},
    }
    mock_aoi_model.get_ee_features.return_value = (main_features, secondary_features)

    mock_seplan.get_benefits_list.return_value = [
        (_img(), "Benefit 1"),
        (_img(), "Benefit 2"),
        (_img(), "Benefit 3"),
    ]
    mock_seplan.get_costs_list.return_value = [
        (_img(), "Cost 1"),
        (_img(), "Cost 2"),
    ]
    mock_seplan.get_masked_constraints_list.return_value = [
        (_img(), "Constraint 1"),
        (_img(), "Constraint 2"),
    ]
    mock_seplan.get_constraint_index.return_value = _img()

    return mock_recipe


@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", [1, 2, 3])
async def test_batched_processing(batch_size):
    """Test that batched processing returns correct structure for each batch size."""
    from component.scripts.statistics import _get_summary_statistics_batched

    mock_recipe = create_mock_recipe()
    mock_gee_interface = Mock()

    call_count = [0]

    async def mock_get_info_async(obj):
        call_count[0] += 1
        await asyncio.sleep(0.01)
        if call_count[0] == 1:
            return {"values": [100, 200, 300], "total": 600}
        return {
            f"Item {call_count[0]}": {
                "values": {"mean": 50, "sum": 100, "percent": 25},
                "total": [1000],
            }
        }

    mock_gee_interface.get_info_async = AsyncMock(side_effect=mock_get_info_async)

    call_count[0] = 0
    result = await _get_summary_statistics_batched(
        mock_gee_interface, mock_recipe, batch_size=batch_size
    )

    assert "test_recipe" in result
    assert len(result["test_recipe"]) == 3

    for aoi_name, aoi_data in result["test_recipe"].items():
        assert "suitability" in aoi_data
        assert "benefit" in aoi_data
        assert "cost" in aoi_data
        assert "constraint" in aoi_data
        assert "color" in aoi_data


@pytest.mark.asyncio
async def test_fallback_on_429_error():
    """Test that fallback is triggered on 429 errors."""
    from component.scripts.statistics import get_summary_statistics_async

    mock_recipe = create_mock_recipe()
    # Simplify to single AOI for fallback test
    main_features = {"Main AOI": {"ee_feature": _fc(), "color": "#FF0000"}}
    mock_recipe.seplan.aoi_model.get_ee_features.return_value = (main_features, {})
    mock_recipe.seplan.get_benefits_list.return_value = [(_img(), "Benefit 1")]
    mock_recipe.seplan.get_costs_list.return_value = [(_img(), "Cost 1")]
    mock_recipe.seplan.get_masked_constraints_list.return_value = [
        (_img(), "Constraint 1")
    ]

    mock_gee_interface = Mock()
    attempt = [0]

    async def mock_get_info_async_with_error(obj):
        attempt[0] += 1
        if attempt[0] == 1:
            raise Exception(
                "Request failed with error: {'code': 429, 'message': 'Too many concurrent aggregations.'}"
            )
        await asyncio.sleep(0.01)
        return {"Item": {"values": {"mean": 50}, "total": [1000]}}

    mock_gee_interface.get_info_async = AsyncMock(
        side_effect=mock_get_info_async_with_error
    )

    with patch("component.scripts.statistics.logger"):
        result = await get_summary_statistics_async(mock_gee_interface, mock_recipe)

    assert "test_recipe" in result
    assert "Main AOI" in result["test_recipe"]
    assert attempt[0] > 1, "Should have retried after 429 error"
