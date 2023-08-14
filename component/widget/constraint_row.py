import ee
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

import component.parameter.gui_params as cp
from component.message import cm
from component.model.aoi_model import SeplanAoi
from component.model.constraint_model import ConstraintModel
from component.widget import custom_widgets as cw
from component.widget.alert_state import Alert

from .constraint_dialog import ConstraintDialog
from .constraint_widget import ConstraintWidget


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
    ) -> None:
        # get the models as a member

        self.tag = "tr"
        self.attributes = {"layer_id": layer_id}

        super().__init__()

        self.model = model
        self.dialog = dialog
        self.aoi_model = aoi_model
        self.alert = alert

        idx = model.get_index(id=layer_id)

        # extract information from the model
        self.name = self.model.names[idx]
        self.unit = self.model.units[idx]
        self.layer_id = self.model.ids[idx]
        self.value = self.model.values[idx]
        self.data_type = self.model.data_type[idx]
        self.asset = self.model.assets[idx]

        self.update_view()

    def update_view(self):
        """Create the view of the widget based on the model."""
        # create the crud interface
        self.edit_btn = cw.TableIcon("mdi-pencil", self.layer_id)
        self.delete_btn = cw.TableIcon("mdi-trash-can", self.layer_id)
        self.edit_btn.class_list.add("mr-2")

        # create Maskout widget
        self.w_maskout = ConstraintWidget(
            data_type=self.data_type,
            layer_id=self.layer_id,
            v_model=self.value,
        )

        self.get_limits()

        td_list = [
            sw.Html(tag="td", children=[self.edit_btn, self.delete_btn]),
            sw.Html(tag="td", children=[self.name + f" ({self.unit})"]),
            sw.Html(tag="td", children=[self.w_maskout]),
        ]

        self.children = td_list

        # add js behaviour
        self.delete_btn.on_event("click", self.on_delete)
        self.edit_btn.on_event("click", self.on_edit)
        self.w_maskout.observe(self.update_value, "v_model")
        self.aoi_model.observe(self.get_limits, "updated")

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

        self.dialog.value = True
        self.dialog.fill(
            theme=self.model.themes[idx],
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
            unit=self.model.units[idx],
            data_type=self.model.data_type[idx],
        )

    def update_value(self, widget, *args):
        """Update the value of the model."""
        self.model.update_value(self.layer_id, self.w_maskout.v_model)

    @sd.need_ee
    def get_limits(self, *args) -> None:
        """Get the min and max value of the asset in the aoi."""
        # if there's no AOI we'll assume we are in the default constraint
        # and we will return the default value
        if not self.aoi_model.feature_collection:
            # TODO: consider here add
            self.w_maskout.v_model = [0]
            self.update_value(None)
            return

        print(self.data_type)

        if self.data_type in ["binary", "continuous"]:
            reducer = ee.Reducer.minMax()

            def get_value(reduction):
                return list(reduction.getInfo().values())

        else:
            reducer = ee.Reducer.frequencyHistogram()

            def get_value(reduction):
                return (
                    ee.Dictionary(
                        reduction.get(ee.Image(self.asset).bandNames().get(0))
                    )
                    .keys()
                    .getInfo()
                )

        ee_image = ee.Image(self.asset).select(0)
        geom = self.aoi_model.feature_collection

        values = get_value(
            ee_image.reduceRegion(
                reducer=reducer,
                geometry=geom,
                scale=ee_image.projection().nominalScale().multiply(2),
                maxPixels=1e13,
            )
        )

        if self.data_type == "binary":
            if not all(val in values for val in [0, 1]):
                raise Exception("Binary asset must have only 0 and 1 values")
            self.w_maskout.v_model = [values[1]]

        elif self.data_type == "categorical":
            if len(values) > 256:
                raise Exception("Categorical asset must have less than 256 values")
            # todo: depending on the scale of the reductions we could get
            # float values, we need to round them to int, and then remove duplicates
            values = sorted([int(val) for val in values])

            self.w_maskout.items = values

        elif self.data_type == "continuous":
            # There's no way to set min, max as float,
            values = [int(val) for val in values]
            self.w_maskout.widget.max_ = values[0]
            self.w_maskout.widget.min_ = values[-1]

            # when the widget is created for the first time the v_model will be empty,
            # in that case we'll overwrite it with the calculated values.
            # If user changes the values, the model will be updated and we won't overwrite it
            if not self.w_maskout.widget.v_model:
                self.w_maskout.widget.v_model = [values[-1], values[0]]

            if (values[0] - values[-1]) == 1:
                self.w_maskout.widget.step = 0
            else:
                self.w_maskout.widget.step = 1

        self.update_value(None)
