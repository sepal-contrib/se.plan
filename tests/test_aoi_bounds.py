"""Regression test for async AOI extent retrieval.

The admin/zoom path computed bounds via ``feature_collection.geometry()``
(EE's ``Collection.geometry``), which dissolves the whole AOI and exceeds the
2M-edge limit for dense GAUL 2024 boundaries (e.g. Indonesia, ~2.4M edges).
``AoiModel.total_bounds_async`` derives the extent from per-feature bounding
boxes via the async ``gee_interface`` instead, so the kernel thread never
blocks and large countries don't raise.
"""

import pygaul
import pytest

from component.model.aoi_model import AoiModel


@pytest.mark.asyncio
async def test_total_bounds_async_handles_dense_aoi():
    """A dense admin boundary must not blow EE's 2M-edge dissolve limit."""
    model = AoiModel(folder="projects/test/assets")
    # GAUL 2024 code for Indonesia (was 116 in GAUL 2015)
    model.feature_collection = pygaul.AdmItems(admin="241")

    minx, miny, maxx, maxy = await model.total_bounds_async()

    # Indonesia spans roughly 95E-141E and 11S-6N
    assert 94 < minx < 96
    assert -12 < miny < -10
    assert 140 < maxx < 142
    assert 5 < maxy < 7
