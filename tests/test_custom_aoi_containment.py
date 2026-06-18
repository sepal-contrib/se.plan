"""Regression: sub-AOI containment must not dissolve a dense primary AOI."""

import ee
import pygaul
import pytest

from component.widget.custom_aoi_dialog import _outside_area

# small polygon fully inside Java land; polygon crossing into the ocean
_INSIDE = ee.Geometry.Polygon(
    [[[110.0, -7.0], [110.1, -7.0], [110.1, -7.1], [110.0, -7.1]]]
)
_OCEAN = ee.Geometry.Polygon(
    [[[110.0, -8.5], [110.3, -8.5], [110.3, -8.9], [110.0, -8.9]]]
)


def test_outside_area_avoids_dense_primary_dissolve():
    primary = pygaul.AdmItems(name="Indonesia")

    # the naive dissolve blows the 2M-edge limit on a dense primary ...
    with pytest.raises(ee.EEException):
        _INSIDE.difference(primary.geometry(), maxError=1).area().getInfo()

    # ... but the fix does not: ~0 m² outside for a contained child,
    # a large area for one that crosses into the ocean.
    assert _outside_area(_INSIDE, primary).getInfo() < 1.0
    assert _outside_area(_OCEAN, primary).getInfo() > 1e6
