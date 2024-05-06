from typing_extensions import Self

from sepal_ui.aoi.aoi_view import AoiView
from sepal_ui.scripts import decorator as sd
from sepal_ui import sepalwidgets as sw
from sepal_ui.message import ms

from component.message import cm
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn


class ImportAoiDialog(BaseDialog):
    """Dialog wrapper for AoiView used on the map to import a custom AOI from
    the user's assets."""

    def __init__(self, custom_aoi_dialog):
        super().__init__()
        self.attributes = {"id": "import_aoi_dialog"}

        # create the widgets
        title = sw.CardTitle(children=[cm.map.dialog.import_.title])

        # Create table to show the custom geometries
        self.aoi_view = ImportAoiView(custom_aoi_dialog=custom_aoi_dialog)

        text = sw.CardText(children=[self.aoi_view])
        btn_cancel = TextBtn(cm.map.dialog.drawing.cancel, outlined=True)
        action = sw.CardActions(children=[sw.Spacer(), btn_cancel])
        card = sw.Card(class_="ma-0", children=[title, text, action])

        self.children = [card]

        # add js behavior
        btn_cancel.on_event("click", lambda *_: self.close_dialog())

        self.aoi_view.observe(lambda *_: self.close_dialog(), "updated")

    def open_dialog(self, *_):
        """Reset AOI view and open the dialog."""

        self.aoi_view.reset()
        super().open_dialog()


class ImportAoiView(AoiView):
    """This class is a wrapper of the AoiModel that aims to not generate
    the client geometry when the aoi is selected"""

    def __init__(self, custom_aoi_dialog, **kwargs):

        methods = ["-POINTS"]
        self.elevation = False

        super().__init__(methods=methods, **kwargs)

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

        feature_collection = self.model.gdf.__geo_interface__
        name = self.model.name

        self.custom_aoi_dialog.on_new_geom(
            feature_collection=feature_collection, name=name
        )
