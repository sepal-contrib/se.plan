import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from traitlets import Bool, link

from component import model as cmod
from component import parameter as cp
from component.message import cm
from component.scripts.ui_helpers import set_default_asset
from component.widget.alert_state import Alert
from component.widget.base_dialog import BaseDialog


class CostDialog(BaseDialog):
    _COSTS = pd.read_csv(cp.layer_list)
    _COSTS = _COSTS[_COSTS.theme == "cost"]

    count = 0

    loading = Bool(False).tag(sync=True)

    def __init__(self, model: cmod.CostModel, alert: Alert):
        super().__init__()
        # save the model as a member
        self.model = model

        # create an alert to display informations to the user
        self.w_alert = alert

        # create the title
        w_title = sw.CardTitle(children=[cm.cost.dialog.title])

        # create the content
        self.w_name = sw.Combobox(label=cm.cost.dialog.name, items=[], v_model=None)
        default_layers = self._COSTS.layer_id.unique().tolist()
        self.w_name.items = [cm.layers[ly].name for ly in default_layers]
        self.w_id = sw.TextField(v_model=None, readonly=True, viz=False)
        self.w_asset = sw.AssetSelect(types=["IMAGE"])
        self.w_desc = sw.Textarea(label=cm.cost.dialog.desc, v_model=None)
        self.w_unit = sw.TextField(
            label=cm.cost.dialog.unit,
            v_model=self.model._unit,
            readonly=True,
            hint="All cost layer must use the same unit if not aggregation will not be possible",
            persistent_hint=True,
        )
        w_content = sw.CardText(
            children=[
                self.w_name,
                self.w_id,
                self.w_asset,
                self.w_desc,
                self.w_unit,
            ]
        )

        # create the actions
        self.w_validate = sw.Btn(
            cm.cost.dialog.validate, "fa-solid fa-check", type_="success"
        )
        self.w_cancel = sw.Btn(
            cm.cost.dialog.cancel, "fa-solid fa-times", type_="error"
        )
        w_actions = sw.CardActions(
            children=[sw.Spacer(), self.w_validate, self.w_cancel]
        )

        card = sw.Card(children=[w_title, w_content, w_actions])
        link((self, "loading"), (card, "loading"))

        self.children = [card]

        # decorate the validate method with self buttons
        self.validate = sd.loading_button(alert=self.w_alert, button=self.w_validate)(
            self.validate
        )

        # add JS behaviour
        self.w_validate.on_event("click", self.validate)
        self.w_cancel.on_event("click", self.close_dialog)
        self.w_name.observe(self.name_change, "v_model")
        self.w_asset.observe(self.on_asset_change, "v_model")

    def on_asset_change(self, change) -> None:
        """Set the default data type depending on the asset."""
        # check if the asset is in the default list of layers

        if change["new"] in self._COSTS.gee_asset.tolist():
            self.set_readonly(True)
        else:
            self.set_readonly(False)

    def set_readonly(self, value) -> None:
        """Set all the widgets to read only."""
        self.w_desc.readonly = value
        self.w_desc.disabled = value
        self.w_unit.readonly = value
        self.w_unit.disabled = value

    def validate(self, *args) -> None:
        """save the layer in the model (update or add)."""
        # check values are set
        if not all(
            [
                self.w_name.v_model,
                self.w_desc.v_model,
            ]
        ):
            raise Exception(cm.cost.dialog.missing_data)

        # if layer has no layer_id, it needs to be created using the number stored
        # in the object
        if not self.w_id.v_model:
            self.w_id.v_model = f"custom_cost_{self.count}"
            self.count += 1

        # decide either it's an update or a new one
        kwargs = {
            "name": self.w_name.v_model,
            "id": self.w_id.v_model,
            "asset": self.w_asset.v_model,
            "desc": self.w_desc.v_model,
        }
        if self.w_id.v_model in self.model.ids:
            self.model.update(**kwargs)
        else:
            self.model.add(**kwargs)

        # close the dialog
        self.close_dialog()

    def open_new(self, *args) -> None:
        """open new dialog with default values."""
        # reset the alert
        self.w_alert.reset()

        # reset the fields, 4 means the number of widgets to reset
        self.fill(*[None] * 4)

        # open the dialog
        self.open_dialog()

    def name_change(self, *args) -> None:
        """if the selected layer is from the combo box items, select all the default informations."""
        if not self.w_name.v_model:
            self.fill(self.w_name.items[0], *[""] * 3)
            return

        if self.w_name.v_model not in self.w_name.items:
            return

        # get the information from the dataframe
        layer_id = next(
            k for k, ly in cm.layers.items() if ly.name == self.w_name.v_model
        )
        cost = self._COSTS[self._COSTS.layer_id == layer_id].iloc[0]

        # fill the different widgets
        self.w_id.v_model = layer_id

        # Set the default asset
        self.w_asset.v_model = cost.gee_asset
        self.w_asset.items = set_default_asset(self.w_asset.items, cost.gee_asset)

        self.w_desc.v_model = cm.layers[layer_id].detail

    def fill(self, name: str, id: str, asset: str, desc: str) -> None:
        """fill the dialog with data from the link."""
        self.w_name.v_model = name
        self.w_id.v_model = id
        self.w_asset.v_model = asset
        self.w_desc.v_model = desc

        if asset == "":
            if {"header": cm.default_asset_header} in self.w_asset.items:
                self.w_asset.items = self.w_asset.items[2:][:]
