"""AOI geometry helpers that avoid EE's 2M-edge ``Collection.geometry`` limit.

``ee.FeatureCollection.geometry()`` aggregates every feature into one geometry,
which can exceed EE's 2M-edge limit for dense AOIs. These helpers materialise
only per-feature bounding boxes, so they stay under the cap. Kept dependency-free
(only ``ee``) so every module can import them at the top level.
"""

from typing import Union

import ee


def _aoi_bbox(aoi: Union[ee.FeatureCollection, ee.Geometry]) -> ee.Geometry:
    """Bounding-box geometry for ``reduceRegion`` that never dissolves the AOI.

    ``aoi.geometry()`` unions every feature and can exceed EE's 2M-edge limit on
    dense AOIs. Take each feature's bbox first; callers clip the image to ``aoi``
    so only AOI pixels are reduced (the result matches reducing over the exact
    polygon).
    """
    fc = ee.FeatureCollection(aoi)
    return fc.map(lambda feat: ee.Feature(feat.geometry().bounds())).geometry().bounds()
