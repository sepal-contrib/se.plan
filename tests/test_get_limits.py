"""Regression test: constraint value limits must not dissolve a dense AOI.

``get_limits_async`` reduced a constraint layer over ``geometry=aoi`` (the
primary feature collection), which dissolves the AOI and exceeds EE's 2M-edge
limit for dense GAUL 2024 boundaries (e.g. Indonesia, ~2.4M edges). The fix
clips the image to the AOI and reduces over its bounding box.
"""

import pygaul
import pytest
from sepal_ui.scripts.gee_interface import GEEInterface

from component.scripts.gee import get_limits_async


@pytest.mark.asyncio
async def test_get_limits_async_handles_dense_aoi():
    """Continuous-layer limits over Indonesia must evaluate without dissolving."""
    aoi = pygaul.AdmItems(name="Indonesia")

    # GTOPO30 (~1 km elevation) keeps the dense-AOI reduction fast; the dissolve
    # in the old code failed regardless of the layer's resolution.
    limits = await get_limits_async(GEEInterface(), "USGS/GTOPO30", "continuous", aoi)

    assert len(limits) == 2
    assert limits[0] < limits[1]
