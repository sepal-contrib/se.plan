import logging
from copy import deepcopy
from typing import Optional

import ee
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex
from sepal_ui import sepalwidgets as sw

import component.parameter as cp
from component.frontend.icons import icon
from component.message import cm
from component.scripts.aoi_geometry import fc_from_source
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn

from .custom_geometries_dialog import CustomGeometriesTable
from .map import SeplanMap

logger = logging.getLogger("SEPLAN")

# A sub-AOI is flagged "outside" only when more than this FRACTION of its area
# falls outside the primary AOI. Independent vector datasets never align exactly
# (coastlines / borders from different sources), so a small relative mismatch is
# expected and tolerated; a geometry that is genuinely (largely) outside still
# trips it. Replaces the old fixed 1 m² tolerance, which an imported asset's
# boundary mismatch (~0.005 % of area) would already exceed.
_CONTAINMENT_FRACTION = 0.01


def _outside_area(child: ee.Geometry, primary_fc: ee.FeatureCollection) -> ee.Number:
    """Area (m²) of ``child`` lying outside the primary AOI.

    Sums per-feature covered area instead of differencing against the union of
    the overlapping features: a sub-AOI spanning a dense primary would otherwise
    rebuild the whole multi-million-edge collection and exceed EE's 2M-edge
    limit. Admin features are disjoint, so covered area is the sum of per-feature
    intersections; this stays vector-exact (the sub-m² tolerance is preserved).
    """
    nearby = primary_fc.filterBounds(child)
    with_area = nearby.map(
        lambda feat: feat.set(
            "_a", child.intersection(feat.geometry(), maxError=1).area(maxError=1)
        )
    )
    covered = with_area.aggregate_sum("_a")
    return child.area(maxError=1).subtract(covered)


def _outside_fraction(
    child: ee.Geometry, primary_fc: ee.FeatureCollection
) -> ee.Number:
    """Fraction (0-1) of ``child``'s area lying outside the primary AOI."""
    area = child.area(maxError=1)
    return _outside_area(child, primary_fc).divide(area.max(1))


class CustomAoiDialog(BaseDialog):
    feature: dict = None
    "feature collection of new geometry imported from ImportAoiDialog."

    def __init__(self, map_: SeplanMap):
        super().__init__()
        self.attributes = {"id": "custom_aoi_dialog"}
        self.map_ = map_

        # create the widgets
        self.btn = TextBtn(cm.map.dialog.drawing.btn, gliph=icon("check"))
        title = sw.CardTitle(children=[cm.map.dialog.drawing.title])
        # Create table to show the custom geometries
        table = CustomGeometriesTable(self.map_)
        self.w_name = sw.TextField(
            label=cm.map.dialog.drawing.label, v_model=None, class_="mr-2"
        )

        self.save_input = sw.Flex(
            class_="d-flex align-center",
            children=[
                self.w_name,
                self.btn,
            ],
        )
        # Alert area for containment-check errors. Stays empty in the happy path.
        self.alert = sw.Alert()
        text = sw.CardText(children=[table, self.save_input, self.alert])
        btn_cancel = TextBtn(cm.map.dialog.drawing.cancel, outlined=True)
        action = sw.CardActions(children=[sw.Spacer(), btn_cancel])
        card = sw.Card(class_="ma-0", children=[title, text, action])

        self.children = [card]

        # Holds the in-flight validation task between kick-off and completion
        self._validate_task = None
        # Monotonic token: rejects a validation verdict that settles after the
        # user cancelled or started a newer save.
        self._validate_gen = 0

        # Set by ``on_new_geom`` when the admin-sub flow forwards a feature
        # whose containment is structurally guaranteed; ``on_save_geom``
        # honors it by bypassing the GEE check.
        self._skip_containment_check = False

        # Descriptor (asset id / admin code) carried from on_new_geom to
        # on_save_geom so analysis + tiles can rebuild the exact geometry.
        self._pending_source = None

        # add js behavior
        btn_cancel.on_event("click", self.on_cancel)
        self.btn.on_event("click", self.on_save_geom)

        self.map_.observe(self.on_new_geom, "new_geom")

    def on_save_geom(self, *_):
        """Stage the candidate features and kick off the GEE containment check.

        The actual append to ``map_.custom_layers`` happens in
        ``_commit_save`` once ``_validate_async`` confirms every drawn /
        imported feature lies within the primary AOI. The dialog stays open
        on validation failure so the user can adjust without losing context.
        """
        if self.feature:
            features = self.feature["features"]
            # Increase the new_geom counter but don't trigger the event
            self.map_.unobserve(self.on_new_geom, "new_geom")
            self.map_.new_geom += 1
            self.map_.observe(self.on_new_geom, "new_geom")
        else:
            features = self.map_.dc.to_json()["features"]

        if not features:
            return

        geom_number = self.map_.new_geom
        aoi_color = to_hex(plt.cm.tab10(geom_number))
        style = {
            **cp.aoi_style,
            "color": aoi_color,
            "fillColor": aoi_color,
        }
        for feature in features:
            feature["properties"]["id"] = geom_number
            feature["properties"]["name"] = self.w_name.v_model
            feature["properties"]["style"] = style
            feature["properties"]["hover_style"] = {
                **style,
                "fillOpacity": 0.4,
                "weight": 2,
            }
            # Descriptor to rebuild the EXACT geometry server-side for analysis
            # + tile rendering (None for drawn geometries — their geojson is
            # already exact). The stored geometry itself stays simplified.
            feature["properties"]["source"] = getattr(self, "_pending_source", None)

        self._candidate_features = features
        self.alert.reset()

        gee_interface = getattr(self.map_, "gee_interface", None)
        primary_fc = getattr(self.map_.aoi_model, "feature_collection", None)

        # Skip the GEE round-trip in any of:
        #   - No GEE session / no primary AOI (defensive fallback).
        #   - The admin-sub path opted out (containment is structural).
        if self._skip_containment_check or gee_interface is None or primary_fc is None:
            self._commit_save()
            return

        self.btn.disabled = True
        self.btn.loading = True
        # Supersede any in-flight validation; the token lets us reject a verdict
        # that settles after the user cancelled (the cancel button stays enabled).
        if self._validate_task is not None:
            self._validate_task.cancel()
        self._validate_gen += 1
        gen = self._validate_gen
        self._validate_task = gee_interface.create_task(
            func=lambda: self._validate_async(gen),
            key="custom_geom_validate",
            on_done=self._on_validate_done,
            on_error=lambda exc: self._on_validate_error(exc, gen),
        )
        self._validate_task.start()

    async def _validate_async(self, gen):
        """Return the count of staged sub-AOIs that fall (largely) outside the primary.

        Uses the EXACT geometry, rebuilt server-side from the ``source``
        descriptor (asset id / admin code). The stored geojson is *simplified*
        and its distortion produced false "outside" verdicts on near-boundary
        features. Drawn geometries have no source, so their exact geojson is used
        directly. A relative threshold (``_CONTAINMENT_FRACTION``) tolerates
        boundary mismatches between independent datasets.
        """
        primary_fc = self.map_.aoi_model.feature_collection
        gee_interface = self.map_.gee_interface
        feats = self._candidate_features or []

        # Import/admin: every candidate feature shares one source, so rebuild and
        # check the exact reconstructed FC once. Draw: each exact geojson feature.
        source = feats[0]["properties"].get("source") if feats else None
        if source:
            child = fc_from_source(source, feats[0]).geometry(maxError=1)
            frac = await gee_interface.get_info_async(
                _outside_fraction(child, primary_fc)
            )
            outside = 1 if (frac is not None and frac > _CONTAINMENT_FRACTION) else 0
            return {"gen": gen, "outside_count": outside}

        outside_count = 0
        for feat in feats:
            child = ee.Geometry(feat["geometry"])
            frac = await gee_interface.get_info_async(
                _outside_fraction(child, primary_fc)
            )
            if frac is not None and frac > _CONTAINMENT_FRACTION:
                outside_count += 1
        return {"gen": gen, "outside_count": outside_count}

    def _on_validate_done(self, result: dict):
        """Commit on full containment, otherwise surface the failure."""
        # Reject a verdict whose save the user cancelled or superseded.
        if not result or result["gen"] != self._validate_gen:
            return
        outside_count = result["outside_count"]
        self.btn.disabled = False
        self.btn.loading = False
        if outside_count > 0:
            noun = "geometry" if outside_count == 1 else "geometries"
            verb = "is" if outside_count == 1 else "are"
            self.alert.add_msg(
                f"{outside_count} {noun} {verb} outside the primary area of "
                "interest. Adjust the drawing (or pick a different AOI) and "
                "try again.",
                type_="error",
            )
            return
        self._commit_save()

    def _on_validate_error(self, exc: Exception, gen: int):
        """Surface the GEE error in the dialog without silently saving."""
        if gen != self._validate_gen:  # superseded/cancelled — drop stale error
            return
        self.btn.disabled = False
        self.btn.loading = False
        logger.exception("Custom geometry validation failed", exc_info=exc)
        self.alert.add_msg(
            f"Could not verify the geometry against the primary AOI: {exc}",
            type_="error",
        )

    def _commit_save(self):
        """Append validated features to ``map_.custom_layers`` and close."""
        features = getattr(self, "_candidate_features", None) or []
        if features:
            current_feats = deepcopy(self.map_.custom_layers)
            current_feats["features"] += features
            self.map_.custom_layers = current_feats
            # zoom to the freshly added sub-AOI (async, exact geometry)
            self.map_.zoom_to_custom(features)
        self._candidate_features = None
        self.on_cancel()

    def on_cancel(self, *_):
        """Clear any in-progress drawing and remove the Geoman toolbar.

        ``dc.clear()`` discards any draft features so they don't reappear
        the next time the toolbar is shown; ``dc.hide()`` also pops the
        toolbar off ``map_.controls`` so the user gets a clean map back
        after committing or cancelling the custom geometry.
        """
        self.map_.dc.clear()
        self.map_.dc.hide()

        # Invalidate + cancel any in-flight validation so it can't commit/alert
        # after the user cancelled.
        self._validate_gen += 1
        if self._validate_task is not None:
            self._validate_task.cancel()

        # Clear any feature that was selected
        self.feature = None
        self._candidate_features = None
        self._skip_containment_check = False
        self._pending_source = None

        # Reset transient validation UI
        self.btn.disabled = False
        self.btn.loading = False
        self.alert.reset()

        # Close the dialog
        self.close_dialog()

    def open_dialog(
        self,
        new_geom: bool,
        *_,
    ):
        """Open dialog in two different ways."""
        # hide save element and only show table
        self.save_input.show() if new_geom else self.save_input.hide()

        super().open_dialog()

    def on_new_geom(
        self,
        *_,
        feature_collection: Optional[dict] = None,
        name: Optional[str] = None,
        skip_containment_check: bool = False,
        source: Optional[dict] = None,
    ):
        """Read the aoi and give a default name.

        Manages new geometries drawn by the user, custom ones imported via
        ``ImportAoiDialog``, and admin sub-areas forwarded from
        ``AdminAoiDialog``.

        Args:
            feature_collection: Optional GeoJSON ``FeatureCollection`` dict
                from the import / admin paths. Its geometry is SIMPLIFIED (for
                display / hover only); analysis uses ``source`` instead.
            name: Suggested name when ``feature_collection`` is provided.
            skip_containment_check: If True, ``on_save_geom`` will skip the
                GEE containment check. Used by the admin-sub path where
                hierarchy guarantees the geometry sits inside the primary AOI.
            source: Descriptor used to rebuild the EXACT geometry server-side
                for analysis + tile rendering (``{"type": "asset"|"admin", ...}``).
                ``None`` for drawn geometries (their geojson is already exact).
                Stored on each feature's ``properties["source"]``.
        """
        # Count the number of geometries in map_.custom_layers
        index = len(self.map_.custom_layers["features"]) + 1

        if not feature_collection:
            aoi_name = f"Custom AOI {index}"
        else:
            aoi_name = f"Custom_{name}"
            self.feature = feature_collection

        self._skip_containment_check = skip_containment_check
        self._pending_source = source
        self.w_name.v_model = aoi_name
        self.open_dialog(new_geom=True)
