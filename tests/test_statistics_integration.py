"""Integration tests for statistics computation with real GEE objects.

Run with: .nox/test/bin/pytest tests/test_statistics_integration.py -v
Requires Earth Engine credentials.
"""

import pytest
import ee
import logging
from unittest.mock import Mock

from component.scripts.statistics import (
    get_summary_statistics_async,
    _get_summary_statistics_sequential,
    _get_summary_statistics_batched,
    get_image_stats,
    get_image_mean,
    get_image_sum,
    get_image_percent_cover_pixelarea,
)
from sepal_ui.scripts.gee_interface import GEEInterface

logger = logging.getLogger("TEST")


@pytest.fixture(scope="session")
def gee_initialized():
    """Initialize Earth Engine once for all tests."""
    try:
        ee.Initialize()
        return True
    except Exception as e:
        pytest.skip(f"Could not initialize Earth Engine: {e}")


@pytest.fixture
def gee_interface(gee_initialized):
    """Create a GEEInterface instance."""
    return GEEInterface()


@pytest.fixture
def simple_test_image(gee_initialized):
    """Create a simple test image (SRTM elevation)."""
    return ee.Image("USGS/SRTMGL1_003").select("elevation")


@pytest.fixture
def test_geometry(gee_initialized):
    """Create a small test geometry."""
    return ee.Geometry.Rectangle([-122.5, 37.5, -122.4, 37.6])


@pytest.fixture
def test_feature_collection(test_geometry):
    """Create a feature collection for testing."""
    return ee.FeatureCollection([ee.Feature(test_geometry)])


@pytest.fixture
def mock_recipe(simple_test_image, test_feature_collection):
    """Create a mock recipe with real GEE objects."""
    recipe = Mock()
    recipe.recipe_session_path = "/tmp/test"
    recipe.get_recipe_name.return_value = "integration_test_recipe"

    seplan = Mock()
    recipe.seplan = seplan

    aoi_model = Mock()
    seplan.aoi_model = aoi_model

    main_features = {
        "Test AOI": {"ee_feature": test_feature_collection, "color": "#FF0000"}
    }
    aoi_model.get_ee_features.return_value = (main_features, {})

    scaled_image = simple_test_image.divide(100)
    seplan.get_benefits_list.return_value = [
        (scaled_image, "Elevation Benefit 1"),
        (scaled_image.multiply(1.5), "Elevation Benefit 2"),
    ]
    seplan.get_costs_list.return_value = [(scaled_image, "Elevation Cost 1")]

    binary_constraint = simple_test_image.gt(100)
    seplan.get_masked_constraints_list.return_value = [
        (binary_constraint, "Elevation Constraint 1")
    ]
    seplan.get_constraint_index.return_value = (
        simple_test_image.divide(500).floor().clamp(1, 5)
    )

    return recipe


# -- Individual stats functions --


@pytest.mark.asyncio
async def test_get_image_stats(simple_test_image, test_geometry, gee_interface):
    """Test get_image_stats with real image."""
    classified = simple_test_image.divide(500).floor().clamp(1, 5).toInt()
    mask = ee.Image(1)

    result_dict = get_image_stats(classified, mask, test_geometry)
    result = await gee_interface.get_info_async(result_dict)

    assert "values" in result
    assert "total" in result
    assert result["total"] > 0


@pytest.mark.asyncio
async def test_get_image_mean(simple_test_image, test_geometry, gee_interface):
    """Test get_image_mean with real image."""
    image = simple_test_image.divide(10)
    mask = ee.Image(1)

    result_dict = get_image_mean(image, test_geometry, mask, "test_mean", True)
    result = await gee_interface.get_info_async(result_dict)

    assert "test_mean" in result
    values = result["test_mean"]["values"]
    assert "mean" in values
    assert "max" in values
    assert "min" in values


@pytest.mark.asyncio
async def test_get_image_sum(simple_test_image, test_geometry, gee_interface):
    """Test get_image_sum with real image."""
    image = simple_test_image.divide(1000)
    mask = ee.Image(1)

    result_dict = get_image_sum(image, test_geometry, mask, "test_sum")
    result = await gee_interface.get_info_async(result_dict)

    assert "test_sum" in result
    assert "sum" in result["test_sum"]["values"]


@pytest.mark.asyncio
async def test_get_image_percent_cover(test_geometry, gee_interface):
    """Test get_image_percent_cover_pixelarea with real image."""
    image = ee.Image.random(0).gt(0.5)

    result_dict = get_image_percent_cover_pixelarea(
        image, test_geometry, "test_constraint"
    )
    result = await gee_interface.get_info_async(result_dict)

    assert "test_constraint" in result
    percent = result["test_constraint"]["values"]["percent"]
    assert 0 <= percent <= 100


# -- Batched and sequential processing --


@pytest.mark.asyncio
async def test_batched_processing_batch_size_1(gee_interface, mock_recipe):
    """Test batched processing with batch_size=1."""
    result = await _get_summary_statistics_batched(
        gee_interface, mock_recipe, batch_size=1
    )

    assert "integration_test_recipe" in result
    aoi_result = result["integration_test_recipe"]["Test AOI"]
    assert "suitability" in aoi_result
    assert len(aoi_result["benefit"]) == 2
    assert len(aoi_result["cost"]) == 1
    assert len(aoi_result["constraint"]) == 1


@pytest.mark.asyncio
async def test_batched_processing_batch_size_2(gee_interface, mock_recipe):
    """Test batched processing with batch_size=2."""
    result = await _get_summary_statistics_batched(
        gee_interface, mock_recipe, batch_size=2
    )

    assert "integration_test_recipe" in result
    assert "Test AOI" in result["integration_test_recipe"]


@pytest.mark.asyncio
async def test_sequential_processing(gee_interface, mock_recipe):
    """Test sequential processing."""
    result = await _get_summary_statistics_sequential(gee_interface, mock_recipe)

    assert "integration_test_recipe" in result
    aoi_result = result["integration_test_recipe"]["Test AOI"]
    assert aoi_result["suitability"]["total"] > 0


@pytest.mark.asyncio
async def test_main_entry_point(gee_interface, mock_recipe):
    """Test the main entry point with automatic fallback."""
    result = await get_summary_statistics_async(gee_interface, mock_recipe)

    assert "integration_test_recipe" in result
    assert "Test AOI" in result["integration_test_recipe"]


@pytest.mark.asyncio
async def test_sequential_vs_batched_consistency(gee_interface, mock_recipe):
    """Verify that sequential and batched produce equivalent results."""
    sequential_result = await _get_summary_statistics_sequential(
        gee_interface, mock_recipe
    )
    batched_result = await _get_summary_statistics_batched(
        gee_interface, mock_recipe, batch_size=2
    )

    recipe_name = "integration_test_recipe"
    seq_aoi = sequential_result[recipe_name]["Test AOI"]
    bat_aoi = batched_result[recipe_name]["Test AOI"]

    assert seq_aoi.keys() == bat_aoi.keys()
    assert len(seq_aoi["benefit"]) == len(bat_aoi["benefit"])
    assert len(seq_aoi["cost"]) == len(bat_aoi["cost"])
    assert len(seq_aoi["constraint"]) == len(bat_aoi["constraint"])
