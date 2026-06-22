import logging
from functools import partial

from sepal_ui import sepalwidgets as sw
from sepal_ui.aoi.aoi_view import AoiView
from sepal_ui.message import ms
from typing_extensions import Self

from component.message import cm
from component.scripts.aoi_geometry import simplify_fc
from component.scripts.mem_diagnostics import probe
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn

logger = logging.getLogger("SEPLAN")


class ImportAoiDialog(BaseDialog):
    """Dialog wrapper for AoiView to import a custom AOI from the user's assets."""

    def __init__(self, custom_aoi_dialog, gee_interface=None):
        super().__init__()
        self.attributes = {"id": "import_aoi_dialog"}

        # create the widgets
        title = sw.CardTitle(children=[cm.map.dialog.import_.title])

        # Create table to show the custom geometries
        self.aoi_view = ImportAoiView(
            custom_aoi_dialog=custom_aoi_dialog, gee_interface=gee_interface
        )

        text = sw.CardText(children=[self.aoi_view])
        btn_cancel = TextBtn(cm.map.dialog.drawing.cancel, outlined=True)
        action = sw.CardActions(children=[sw.Spacer(), btn_cancel])
        card = sw.Card(class_="ma-0", children=[title, text, action])

        self.children = [card]

        # Caller-supplied dialog to restore on cancel — set per call to
        # ``open_dialog(return_to=...)``. Cleared whenever it's consumed.
        self._return_to = None

        # add js behavior
        btn_cancel.on_event("click", lambda *_: self._cancel())

        # Successful import → close the dialog (next surface, the rename
        # dialog, opens via CustomAoiDialog.on_new_geom from ImportAoiView).
        # Also clear ``_return_to`` so a later cancel from a different open
        # call doesn't bounce back to a stale picker.
        self.aoi_view.observe(lambda *_: self._on_success(), "updated")

    def _on_success(self):
        self._return_to = None
        self.close_dialog()

    def _cancel(self, *_):
        """Close and re-open the caller dialog if any."""
        self.aoi_view.cancel_import()  # reject any in-flight build that settles late
        return_to = self._return_to
        self._return_to = None
        self.close_dialog()
        if return_to is not None:
            return_to.open_dialog()

    def open_dialog(self, *_, return_to=None):
        """Reset AOI view and open the dialog.

        Args:
            return_to: Optional dialog to re-open if the user cancels.
        """
        if return_to is not None:
            self._return_to = return_to
        self.aoi_view.cancel_import()  # invalidate any leftover in-flight build
        self.aoi_view.reset()
        super().open_dialog()


class ImportAoiView(AoiView):
    """Wrap AoiModel so importing an AOI doesn't materialise client geometry."""

    def __init__(self, custom_aoi_dialog, gee_interface, **kwargs):

        # Admin sub-areas have their own dedicated entry (AdminAoiDialog) — exclude
        # ADMIN0/1/2 here. SHAPE (local vector-file upload) and POINTS are also
        # off: users upload via a GEE asset instead, so the import dialog is
        # focused on ASSET references.
        methods = ["-POINTS", "-ADMIN0", "-ADMIN1", "-ADMIN2", "-SHAPE"]
        self.elevation = False

        super().__init__(methods=methods, gee_interface=gee_interface, **kwargs)

        self.custom_aoi_dialog = custom_aoi_dialog
        self._import_task = None
        # Monotonic token: bumped on each validate / cancel / reopen so a build
        # that settles after the user moved on doesn't pop the rename dialog.
        self._import_gen = 0

    def cancel_import(self) -> None:
        """Invalidate + cancel any in-flight import build (call on cancel/reopen)."""
        self._import_gen += 1
        if self._import_task is not None:
            self._import_task.cancel()

    def _update_aoi(self, *args) -> Self:
        """Import the AOI without materialising full geometry client-side.

        The dense-geometry OOM (and UI freeze) came from pulling the entire
        FeatureCollection down — ``get_info`` -> GeoDataFrame ->
        ``__geo_interface__`` -> ``ee.serializer``. Instead we keep the AOI
        server-side and only pull a SIMPLIFIED outline (via ``simplify_fc``) for
        the hover label, off the kernel thread.

        This view is always GEE-backed and has no ``map_`` of its own — the
        imported AOI is rendered through ``map_.custom_layers`` after
        ``on_new_geom`` — so there is no synchronous / non-GEE branch.
        """
        if self.map_:
            self.model.geo_json = self.aoi_dc.to_json()

        self.model.set_object()  # builds the server-side ee.FeatureCollection

        fc = self.model.feature_collection
        if fc is None:
            return self

        # ASSET: keep the geometry server-side and store a descriptor so analysis
        # + tiles rebuild the EXACT FC; only a SIMPLIFIED outline is pulled for
        # display/hover. SHAPE: a (bounded) local upload with no server-side
        # source — keep its exact geojson so analysis stays exact.
        if self.model.method == "ASSET":
            aj = self.model.asset_json or {}
            source = {
                "type": "asset",
                "id": aj.get("pathname"),
                "column": aj.get("column", "ALL"),
                "value": aj.get("value"),
            }
            dissolve = aj.get("column", "") == "ALL"
            do_simplify = True
        else:
            source = None
            dissolve = False
            do_simplify = False

        # Supersede any in-flight build and capture a fresh token.
        self.cancel_import()
        gen = self._import_gen
        self._set_loading(True)
        # hold a ref so the task isn't GC'd before it runs
        self._import_task = self.model.gee_interface.create_task(
            func=partial(
                self._build_async,
                gen,
                fc,
                self.model.name,
                dissolve,
                do_simplify,
                source,
            ),
            key="import_aoi_build",
            on_error=self._on_build_error,
        )
        self._import_task.start()
        return self

    async def _build_async(self, gen, fc, name, dissolve, do_simplify, source):
        """Pull the display outline server-side, then hand off to the rename dialog.

        Runs on the GEE event loop (via ``create_task``) so the kernel thread
        stays responsive. For an ASSET the outline is SIMPLIFIED (tiny transfer);
        the exact geometry is rebuilt from ``source`` for analysis + tiles. A
        SHAPE keeps its exact (bounded) geojson.
        """
        try:
            display_fc = simplify_fc(fc, dissolve=dissolve) if do_simplify else fc
            with probe("aoi-import-display-geojson"):
                feature_collection = await self.model.gee_interface.get_info_async(
                    display_fc
                )

            # Drop the result if the user cancelled/reopened or re-validated; the
            # completion tail has no further await, so cancel() alone can't stop it.
            if gen != self._import_gen:
                return

            self.alert.add_msg(ms.aoi_sel.complete, "success")
            self.updated += 1
            self.custom_aoi_dialog.on_new_geom(
                feature_collection=feature_collection, name=name, source=source
            )
        finally:
            self._set_loading(False)

    def _on_build_error(self, exc: Exception):
        """Surface import failures in the dialog alert without silently saving."""
        self._set_loading(False)
        logger.exception("AOI import failed", exc_info=exc)
        self.alert.add_msg(str(exc), type_="error")

    def _set_loading(self, loading: bool) -> None:
        """Spin the validate button across the async import (best-effort)."""
        btn = getattr(self, "btn", None)
        if btn is not None:
            btn.loading = loading
            btn.disabled = loading
