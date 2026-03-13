import pandas as pd
from component.frontend.icons import icon
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

from component import parameter as cp
from component.message import cm
from component.model import CostModel
from component.model.aoi_model import SeplanAoi
from component.scripts.seplan import asset_to_image
from component.widget import custom_widgets as cw
from component.widget.alert_state import Alert
from component.widget.cost_dialog import CostDialog

from .preview_map_dialog import PreviewMapDialog


class CostRow(sw.Html):
    _DEFAULT_LAYERS = pd.read_csv(cp.layer_list).layer_id

    def __init__(
        self,
        model: CostModel,
        layer_id: str,
        dialog: CostDialog,
        aoi_model: SeplanAoi,
        alert: Alert,
        preview_map: PreviewMapDialog,
        *_,
        **__,
    ) -> None:
        self.tag = "tr"
        self.attributes = {"layer_id": layer_id}
        self.layer_id = layer_id

        super().__init__()

        # get the model as a member
        self.model = model
        self.dialog = dialog
        self.preview_map = preview_map
        self.aoi_model = aoi_model
        self.alert = alert

        self.get_model_data()

        # extract information from the model

        self.edit_btn = cw.TableIcon(icon("pencil"), self.layer_id)
        self.delete_btn = cw.TableIcon(icon("close"), self.layer_id)
        self.show_map_btn = cw.TableIcon(icon("map"), self.layer_id)

        self.edit_btn.class_list.add("mr-2")
        self.delete_btn.class_list.add("mr-2")

        self.delete_btn.on_event("click", self.on_delete)
        self.edit_btn.on_event("click", self.on_edit)
        self.show_map_btn.on_event("click", self.on_show_map)

        self.update_view()

    def get_model_data(self):
        """Get and set the data of the given layer_id to the row."""
        idx = self.model.get_index(self.layer_id)

        self.name = self.model.names[idx]
        self.asset = self.model.assets[idx]

    @sd.catch_errors()
    def on_show_map(self, *_):
        """Mask constraint with map values and add it to the map."""
        ee_image = asset_to_image(self.asset)
        self.preview_map.show_layer(
            ee_image, "benefit", self.name, self.aoi_model.feature_collection
        )

    def update_view(self):
        """Create the view of the widget based on the model."""
        self.get_model_data()

        td_list = [
            sw.Html(
                tag="td",
                children=[
                    self.edit_btn,
                    self.show_map_btn,
                    self.delete_btn,
                ],
            ),
            sw.Html(tag="td", children=[self.name]),
        ]

        super().__init__(tag="tr", children=td_list)

    @sd.catch_errors()
    def on_delete(self, widget, *_):
        """remove the line from the model and trigger table update."""
        if widget.attributes["data-layer"] in cp.mandatory_layers["cost"]:
            raise Exception(cm.questionnaire.error.mandatory_layer)

        self.model.remove(widget.attributes["data-layer"])

    @sd.switch("loading", on_widgets=["dialog"])
    def on_edit(self, widget, data, event):
        """open the dialog with the data contained in the model."""
        idx = self.model.get_index(widget.attributes["data-layer"])

        self.dialog.fill(
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
        )

        self.dialog.open_dialog(type_="edit")
