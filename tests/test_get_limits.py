"""Regression: get_limits_async must not dissolve a dense AOI."""

import pygaul
import pytest
from sepal_ui.scripts.gee_interface import GEEInterface

from component.scripts.gee import get_limits_async


@pytest.mark.asyncio
async def test_get_limits_async_handles_dense_aoi():
    """Continuous-layer limits over Indonesia must evaluate without dissolving."""
    aoi = pygaul.AdmItems(name="Indonesia")

    # GTOPO30 (~1 km) keeps the dense-AOI reduction fast
    limits = await get_limits_async(GEEInterface(), "USGS/GTOPO30", "continuous", aoi)

    assert len(limits) == 2
    assert limits[0] < limits[1]
