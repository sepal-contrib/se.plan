"""Regression: suitability normalization must not dissolve a dense AOI."""

import ee
import pygaul

from component.scripts.seplan import _percentile


def test_percentile_normalization_handles_dense_aoi():
    """_percentile over Indonesia must evaluate without the 2M-edge dissolve."""
    aoi = pygaul.AdmItems(name="Indonesia")
    image = ee.Image("USGS/SRTMGL1_003")

    normalized = _percentile(image, aoi, scale=10000)

    # sampling the output forces the internal reduceRegion (the call that dissolved)
    value = normalized.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=ee.Geometry.Point([107.6, -6.9]),
        scale=1000,
    ).getInfo()

    assert value is not None
