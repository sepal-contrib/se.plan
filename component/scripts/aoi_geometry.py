"""AOI geometry helpers that avoid EE's 2M-edge ``Collection.geometry`` limit.

``ee.FeatureCollection.geometry()`` aggregates every feature into one geometry,
which can exceed EE's 2M-edge limit for dense AOIs. These helpers materialise
only per-feature bounding boxes, so they stay under the cap. Kept dependency-free
(only ``ee``) so every module can import them at the top level.
"""

from typing import Optional, Union

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


# Display simplification tolerance (meters). Dense AOIs (millions of vertices)
# are simplified server-side to a low-vertex outline so only a tiny geometry is
# ever pulled client-side for the map + hover label. The analysis still runs on
# the full-resolution server-side ``ee.FeatureCollection``.
DISPLAY_SIMPLIFY_MAX_ERROR = 1000.0


def simplify_fc(
    aoi: Union[ee.FeatureCollection, ee.Geometry],
    max_error: float = DISPLAY_SIMPLIFY_MAX_ERROR,
    dissolve: bool = False,
) -> ee.FeatureCollection:
    """Per-feature, server-side geometry simplification for client display.

    Materialising a dense AOI client-side (``get_info`` -> GeoDataFrame ->
    ``__geo_interface__`` -> ``ee.serializer``) pulls millions of vertices into
    native + Python memory and OOM-kills the process. Simplifying each feature on
    the server first means ``get_info`` only ever transfers a low-vertex outline.

    Per-feature simplification (not ``Collection.geometry().simplify``) avoids
    EE's 2M-edge dissolve limit on dense collections.

    Args:
        aoi: source collection / geometry (kept server-side, never downloaded).
        max_error: simplification tolerance in meters.
        dissolve: merge the already-simplified (low-edge) features into a single
            geometry — safe because simplification runs first, so the union stays
            well under EE's 2M-edge limit.

    Returns:
        An ``ee.FeatureCollection`` with simplified geometry, safe to materialise
        via ``get_info``.
    """
    fc = ee.FeatureCollection(aoi)
    simplified = fc.map(
        lambda feat: feat.setGeometry(feat.geometry().simplify(maxError=max_error))
    )
    if dissolve:
        merged = simplified.geometry(maxError=max_error)
        return ee.FeatureCollection([ee.Feature(merged)])
    return simplified


def fc_from_source(source: Optional[dict], feat: dict) -> ee.FeatureCollection:
    """Rebuild the EXACT server-side FeatureCollection for a custom sub-AOI.

    ``custom_layers`` stores a *simplified* display geometry (so dense AOIs never
    sit in client memory). Analysis and tile rendering need the full-resolution
    geometry, so we reconstruct it server-side from a small ``source`` descriptor
    instead of from the simplified geojson:

    * ``{"type": "asset", "id", "column", "value"}`` -> ``ee.FeatureCollection``
      (optionally filtered to one feature) — nothing is downloaded.
    * ``{"type": "admin", "code"}`` -> ``pygaul.AdmItems`` — nothing is downloaded.
    * no/unknown descriptor -> ``geojson_to_ee(feat)``, the stored geojson. DRAW
      sub-AOIs are exact and tiny, so this is correct for them; any other path
      degrades gracefully to the (possibly simplified) displayed geometry.

    Args:
        source: the descriptor stored on the feature's ``properties["source"]``.
        feat: the GeoJSON feature (fallback geometry source).

    Returns:
        A server-side ``ee.FeatureCollection`` at full resolution.
    """
    if source:
        kind = source.get("type")
        if kind == "asset" and source.get("id"):
            fc = ee.FeatureCollection(source["id"])
            column, value = source.get("column", "ALL"), source.get("value")
            if column and column != "ALL" and value is not None:
                fc = fc.filter(ee.Filter.eq(column, value))
            return fc
        if kind == "admin" and source.get("code"):
            import pygaul

            return pygaul.AdmItems(admin=source["code"])

    from sepal_ui.scripts import utils as su

    return ee.FeatureCollection(su.geojson_to_ee(feat))
