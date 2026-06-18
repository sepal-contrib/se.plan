"""Regression: total_bounds_async must not dissolve a dense AOI."""

import pygaul
import pytest

from component.model.aoi_model import AoiModel


@pytest.mark.asyncio
async def test_total_bounds_async_handles_dense_aoi():
    """A dense admin boundary must not blow EE's 2M-edge dissolve limit."""
    model = AoiModel(folder="projects/test/assets")
    model.feature_collection = pygaul.AdmItems(admin="241")  # GAUL 2024 Indonesia

    minx, miny, maxx, maxy = await model.total_bounds_async()

    # Indonesia spans roughly 95E-141E and 11S-6N
    assert 94 < minx < 96
    assert -12 < miny < -10
    assert 140 < maxx < 142
    assert 5 < maxy < 7
