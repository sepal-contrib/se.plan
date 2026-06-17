"""AOI geometry helpers that avoid EE's 2M-edge ``Collection.geometry`` limit.

``ee.FeatureCollection.geometry()`` aggregates every feature into a single
geometry; for dense GAUL 2024 boundaries (e.g. Indonesia, ~2.4M edges) that
exceeds EE's hard 2,000,000-edge limit. The helpers here materialise only
per-feature bounding boxes instead, so they stay under the cap regardless of
AOI density.

Kept dependency-free (only ``ee``) so every module can import it at the top
level — no circular-import gymnastics.
"""

from typing import Union

import ee


def _aoi_bbox(aoi: Union[ee.FeatureCollection, ee.Geometry]) -> ee.Geometry:
    """Bounding-box geometry for ``reduceRegion`` that never dissolves the AOI.

    ``aoi.geometry()`` unions every feature (``Collection.geometry``) and exceeds
    EE's 2M-edge limit for dense GAUL 2024 boundaries (e.g. Indonesia, ~2.4M
    edges). The per-feature bbox merge is a cheap stand-in; callers clip the
    image to ``aoi`` first so only AOI pixels are reduced (a clipped reduction
    over this box matches reducing over the exact polygon — verified to the
    sub-pixel — without ever materialising the union).
    """
    fc = ee.FeatureCollection(aoi)
    return fc.map(lambda feat: ee.Feature(feat.geometry().bounds())).geometry().bounds()
