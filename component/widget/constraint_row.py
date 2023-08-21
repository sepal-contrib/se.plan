from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

import component.parameter.gui_params as cp
import component.scripts.gee as gee
from component.message import cm
from component.model.aoi_model import SeplanAoi
from component.model.constraint_model import ConstraintModel
from component.scripts.seplan import mask_image
from component.widget import custom_widgets as cw
from component.widget.alert_state import Alert

from .constraint_dialog import ConstraintDialog
from .constraint_widget import ConstraintWidget
from .preview_map_dialog import PreviewMapDialog


class ConstraintRow(sw.Html):
    aoi_model: SeplanAoi
    """Custom seplan aoi model, it contains a wrapper to notify when the AOI has changed"""

    def __init__(
        self,
        model: ConstraintModel,
        layer_id: str,
        dialog: ConstraintDialog,
        aoi_model: SeplanAoi,
        alert: Alert,
        preview_map: PreviewMapDialog,
    ) -> None:
        # get the models as a member

        self.tag = "tr"
        self.layer_id = layer_id
        self.attributes = {"layer_id": layer_id}

        super().__init__()

        self.model = model
        self.dialog = dialog
        self.preview_map = preview_map
        self.aoi_model = aoi_model
        self.aoi = None
        self.alert = alert

        self.get_model_data()

        # View

        self.edit_btn = cw.TableIcon("mdi-pencil", self.layer_id)
        self.delete_btn = cw.TableIcon("mdi-trash-can", self.layer_id)
        self.show_map_btn = cw.TableIcon("mdi-map", self.layer_id)

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
        self.unit = self.model.units[idx]
        self.value = self.model.values[idx]
        self.data_type = self.model.data_type[idx]
        self.asset = self.model.assets[idx]

    def on_show_map(self, *_):
        """Mask constraint with map values and add it to the map."""
        masked_layer = mask_image(self.asset, self.data_type, self.value)

        self.preview_map.show_layer(
            masked_layer, "constraint", self.name, self.aoi_model.feature_collection
        )

    def update_view(self):
        """Create the view of the widget based on the model."""
        # create Maskout widget
        self.w_maskout = ConstraintWidget(
            data_type=self.data_type,
            layer_id=self.layer_id,
            v_model=self.value,
        )

        self.set_limits()

        td_list = [
            sw.Html(
                tag="td", children=[self.edit_btn, self.delete_btn, self.show_map_btn]
            ),
            sw.Html(tag="td", children=[self.name + f" ({self.unit})"]),
            sw.Html(tag="td", children=[self.w_maskout]),
        ]

        self.children = td_list

        # add js behaviour
        self.w_maskout.observe(self.update_value, "v_model")
        self.aoi_model.observe(self.set_limits, "updated")

    @sd.catch_errors(debug=True)
    @sd.catch_errors(debug=True)
    def on_delete(self, widget, *_):
        """Remove the line from the model and trigger table update."""
        if widget.attributes["data-layer"] in cp.mandatory_layers["constraint"]:
            raise Exception(cm.questionnaire.error.mandatory_layer)

        self.model.remove(widget.attributes["data-layer"])

    @sd.switch("loading", on_widgets=["dialog"])
    def on_edit(self, widget, data, event):
        """Open the dialog and load data contained in the model."""
        idx = self.model.get_index(widget.attributes["data-layer"])

        self.dialog.open_dialog()
        self.dialog.fill(
            theme=self.model.themes[idx],
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
            unit=self.model.units[idx],
            data_type=self.model.data_type[idx],
        )

    def update_value(self, *_):
        """Update the value of the model."""
        self.model.update_value(self.layer_id, self.w_maskout.v_model)

        self.get_model_data()

    @sd.need_ee
    def set_limits(self, *_) -> None:
        """Get the min and max value of the asset in the aoi."""
        self.aoi = self.aoi_model.feature_collection

        # if there's no AOI we'll assume we are in the default constraint
        # and we will return the default value
        if not self.aoi:
            print("theres no aoi")
            self.w_maskout.v_model = [0]
            self.update_value()
            return

        values = gee.get_limits(self.asset, self.data_type, self.aoi)
        print(values)

        if self.data_type == "binary":
            if not all(val in values for val in [0, 1]):
                raise Exception("Binary asset must have only 0 and 1 values")

            # Let's assume that the first value is the one we want to mask out.
            # ussuallly 0
            self.w_maskout.v_model = [values[0]]

        elif self.data_type == "categorical":
            if len(values) > 256:
                raise Exception("Categorical asset must have less than 256 values")
            self.w_maskout.items = values

        elif self.data_type == "continuous":
            # There's no way to set min, max as float,
            values = [int(val) for val in values]
            self.w_maskout.widget.max_ = values[-1]
            self.w_maskout.widget.min_ = values[0]

            # when the widget is created for the first time the v_model will be empty,
            # in that case we'll overwrite it with the calculated values.
            # If user changes the values, the model will be updated and we won't overwrite it
            if not self.w_maskout.widget.v_model:
                self.w_maskout.widget.v_model = [values[0], values[-1]]

            if (values[-1] - values[0]) == 1:
                self.w_maskout.widget.step = 0
            else:
                self.w_maskout.widget.step = 1

        print("lims:", self.w_maskout.v_model)

        self.update_value()
