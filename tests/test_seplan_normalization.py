"""Regression test: normalizing layers over a dense AOI must not dissolve it.

The suitability-index normalization reduced layers over ``aoi.geometry()``
(EE's ``Collection.geometry``), which dissolves the whole AOI and exceeds the
2M-edge limit for dense GAUL 2024 boundaries (e.g. Indonesia, ~2.4M edges).
The fix clips the image to the AOI and reduces over its bounding box instead —
same pixels, no full-coastline union.
"""

import ee
import pygaul

from component.scripts.seplan import _percentile


def test_percentile_normalization_handles_dense_aoi():
    """_percentile over Indonesia must evaluate without the 2M-edge dissolve."""
    aoi = pygaul.AdmItems(name="Indonesia")
    image = ee.Image("USGS/SRTMGL1_003")

    normalized = _percentile(image, aoi, scale=10000)

    # Sampling the normalized output forces the internal reduceRegion (the
    # global percentiles over the AOI) — the call that used to dissolve.
    value = normalized.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=ee.Geometry.Point([107.6, -6.9]),
        scale=1000,
    ).getInfo()

    assert value is not None
