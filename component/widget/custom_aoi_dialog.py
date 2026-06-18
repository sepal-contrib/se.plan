import logging
from copy import deepcopy

import ee
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex
from sepal_ui import sepalwidgets as sw

import component.parameter as cp
from component.frontend.icons import icon
from component.message import cm
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn

from .custom_geometries_dialog import CustomGeometriesTable
from .map import SeplanMap

logger = logging.getLogger("SEPLAN")

# Tolerance (in m²) for the "outside primary AOI" check. Geoman polygons can
# carry sub-meter rounding error vs. the primary AOI boundary, so anything
# under 1 m² of leakage is treated as inside.
_CONTAINMENT_TOLERANCE_M2 = 1.0


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

        # Set by ``on_new_geom`` when the admin-sub flow forwards a feature
        # whose containment is structurally guaranteed; ``on_save_geom``
        # honors it by bypassing the GEE check.
        self._skip_containment_check = False

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

        self._candidate_features = features
        self.alert.reset()

        gee_interface = getattr(self.map_, "gee_interface", None)
        primary_fc = getattr(self.map_.aoi_model, "feature_collection", None)

        # Skip the GEE round-trip in any of:
        #   - No GEE session / no primary AOI (defensive fallback).
        #   - The admin-sub path opted out (containment is structural).
        if (
            self._skip_containment_check
            or gee_interface is None
            or primary_fc is None
        ):
            self._commit_save()
            return

        self.btn.disabled = True
        self.btn.loading = True
        self._validate_task = gee_interface.create_task(
            func=self._validate_async,
            key="custom_geom_validate",
            on_done=self._on_validate_done,
            on_error=self._on_validate_error,
        )
        self._validate_task.start()

    async def _validate_async(self):
        """Return the count of staged features that fall outside the primary AOI."""
        primary_fc = self.map_.aoi_model.feature_collection
        gee_interface = self.map_.gee_interface

        outside_count = 0
        for feat in self._candidate_features:
            child = ee.Geometry(feat["geometry"])
            outside_area = await gee_interface.get_info_async(
                _outside_area(child, primary_fc)
            )
            if outside_area is not None and outside_area > _CONTAINMENT_TOLERANCE_M2:
                outside_count += 1
        return outside_count

    def _on_validate_done(self, outside_count: int):
        """Commit on full containment, otherwise surface the failure."""
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

    def _on_validate_error(self, exc: Exception):
        """Surface the GEE error in the dialog without silently saving."""
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

        # Clear any feature that was selected
        self.feature = None
        self._candidate_features = None
        self._skip_containment_check = False

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
        feature_collection: dict = None,
        name: str = None,
        skip_containment_check: bool = False,
    ):
        """Read the aoi and give a default name.

        Manages new geometries drawn by the user, custom ones imported via
        ``ImportAoiDialog``, and admin sub-areas forwarded from
        ``AdminAoiDialog``.

        Args:
            feature_collection: Optional GeoJSON ``FeatureCollection`` dict
                from the import / admin paths.
            name: Suggested name when ``feature_collection`` is provided.
            skip_containment_check: If True, ``on_save_geom`` will skip the
                GEE containment check. Used by the admin-sub path where
                hierarchy guarantees the geometry sits inside the primary AOI.
        """
        # Count the number of geometries in map_.custom_layers
        index = len(self.map_.custom_layers["features"]) + 1

        if not feature_collection:
            aoi_name = f"Custom AOI {index}"
        else:
            aoi_name = f"Custom_{name}"
            self.feature = feature_collection

        self._skip_containment_check = skip_containment_check
        self.w_name.v_model = aoi_name
        self.open_dialog(new_geom=True)
