from typing_extensions import Self

from sepal_ui.aoi.aoi_view import AoiView
from sepal_ui.scripts import decorator as sd
from sepal_ui import sepalwidgets as sw
from sepal_ui.message import ms

from component.message import cm
from component.widget.base_dialog import BaseDialog
from sepal_ui.scripts.gee_interface import GEEInterface
from component.widget.buttons import TextBtn


class ImportAoiDialog(BaseDialog):
    """Dialog wrapper for AoiView used on the map to import a custom AOI from
    the user's assets."""

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
        self.aoi_view.reset()
        super().open_dialog()


class ImportAoiView(AoiView):
    """This class is a wrapper of the AoiModel that aims to not generate
    the client geometry when the aoi is selected"""

    def __init__(self, custom_aoi_dialog, gee_interface, **kwargs):

        # Admin sub-areas have their own dedicated entry (AdminAoiDialog) —
        # exclude ADMIN0/1/2 here to keep the import dialog focused on file
        # uploads (SHAPE) and asset references (ASSET). POINTS is also off.
        methods = ["-POINTS", "-ADMIN0", "-ADMIN1", "-ADMIN2"]
        self.elevation = False

        super().__init__(methods=methods, gee_interface=gee_interface, **kwargs)

        self.custom_aoi_dialog = custom_aoi_dialog

    @sd.loading_button()
    def _update_aoi(self, *_) -> Self:
        """Load the object in the model & update the map (if possible)."""
        # read the information from the geojson data
        if self.map_:
            self.model.geo_json = self.aoi_dc.to_json()

        # update the model
        self.model.set_object()

        # update the map
        if self.map_:
            self.map_.remove_layer("aoi", none_ok=True)
            self.map_.zoom_bounds(self.model.total_bounds())
            self.map_.add_layer(self.model.get_ipygeojson(self.map_style))

            self.aoi_dc.hide()

        # tell the rest of the apps that the aoi have been updated
        self.alert.add_msg(ms.aoi_sel.complete, "success")
        self.updated += 1

        # Extract the geometry from the model

        if self.model.method == "ASSET":
            if self.model.asset_json.get("column", "") == "ALL":
                # Dissolve the geometries
                self.model.gdf = self.model.gdf.dissolve()

        feature_collection = self.model.gdf.__geo_interface__
        name = self.model.name

        self.custom_aoi_dialog.on_new_geom(
            feature_collection=feature_collection, name=name
        )
