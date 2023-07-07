import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from traitlets import Bool, link

import component.model as cmod
from component import parameter as cp
from component.message import cm


class ConstraintDialog(sw.Dialog):
    _CONSTRAINTS = pd.read_csv(cp.layer_list)
    _CONSTRAINTS = _CONSTRAINTS[_CONSTRAINTS.theme == "constraint"]

    count = 0
    loading = Bool(False).tag(sync=True)

    def __init__(self, model: cmod.ConstraintModel):
        # save the model as a member
        self.model = model

        # create an alert to display informations to the user
        self.w_alert = sw.Alert()

        # create the title
        w_title = sw.CardTitle(children=[cm.constraint.dialog.title])

        # create the content
        default_theme = self._CONSTRAINTS.subtheme.dropna().unique().tolist()
        theme_names = [
            {"text": cm.subtheme[ly], "value": ly} for ly in default_theme if ly
        ]
        theme_names = theme_names + [{"text": cm.subtheme["custom"], "value": "custom"}]
        self.w_theme = sw.Select(
            label=cm.constraint.dialog.theme,
            items=theme_names,
            class_="on-dialog",
            v_model=None,
        )
        self.w_name = sw.Combobox(
            label=cm.constraint.dialog.name, items=[], v_model=None
        )
        self.w_id = sw.TextField(v_model=None, readonly=True, viz=False)
        self.w_asset = sw.AssetSelect()
        self.w_desc = sw.Textarea(label=cm.constraint.dialog.desc, v_model=None)
        self.w_unit = sw.TextField(
            label=cm.constraint.dialog.unit, v_model=None, class_="mr-2"
        )
        self.w_data_type = sw.Select(
            label=cm.data_type.label,
            items=[
                {"text": cm.data_type[data_type], "value": data_type}
                for data_type in cp.data_types
            ],
            v_model="",
            class_="on-dialog",
        )
        w_content = sw.CardText(
            children=[
                self.w_theme,
                self.w_name,
                self.w_id,
                self.w_asset,
                sw.Flex(class_="d-flex", children=[self.w_unit, self.w_data_type]),
                self.w_desc,
                self.w_alert,
            ]
        )

        # create the actions
        self.w_validate = sw.Btn(
            cm.constraint.dialog.validate, "fa-solid fa-check", type_="success"
        )
        self.w_cancel = sw.Btn(
            cm.constraint.dialog.cancel, "fa-solid fa-times", type_="error"
        )
        w_actions = sw.CardActions(
            children=[sw.Spacer(), self.w_validate, self.w_cancel]
        )

        card = sw.Card(children=[w_title, w_content, w_actions])
        link((self, "loading"), (card, "loading"))

        super().__init__(
            persistent=True,
            value=False,
            max_width="700px",
            children=[card],
        )

        # decorate the validate method with self buttons
        self.validate = sd.loading_button(
            alert=self.w_alert, button=self.w_validate, debug=True
        )(self.validate)

        # add JS behaviour
        self.w_validate.on_event("click", self.validate)
        self.w_cancel.on_event("click", self.cancel)
        self.w_theme.observe(self.theme_change, "v_model")
        self.w_name.observe(self.name_change, "v_model")
        self.w_asset.observe(self.on_asset_change, "v_model")

    def on_asset_change(self, change) -> None:
        """Set the default data type depending on the asset."""
        # check if the asset is in the default list of layers

        if change["new"] in self._CONSTRAINTS.gee_asset.tolist():
            self.w_data_type.v_model = self._CONSTRAINTS[
                self._CONSTRAINTS.gee_asset == change["new"]
            ].data_type.values[0]

            # keep readonly
            self.w_data_type.readonly = True
            self.w_data_type.disabled = True
        else:
            self.w_data_type.readonly = False
            self.w_data_type.disabled = False

    def validate(self, *args) -> None:
        """save the layer in the model (update or add)."""
        # check values are set
        if not all(
            [
                self.w_theme.v_model,
                self.w_name.v_model,
                self.w_desc.v_model,
                self.w_unit.v_model,
                self.w_data_type.v_model,
            ]
        ):
            raise Exception(cm.constraint.dialog.missing_data)

        # if layer has no layer_id, it needs to be created using the number stored
        # in the object
        if not self.w_id.v_model:
            self.w_id.v_model = f"custom_benefit_{self.count}"
            self.count += 1

        # decide either it's an update or a new one
        kwargs = {
            "theme": self.w_theme.v_model,
            "name": self.w_name.v_model,
            "id": self.w_id.v_model,
            "asset": self.w_asset.v_model,
            "desc": self.w_desc.v_model,
            "unit": self.w_unit.v_model,
            "data_type": self.w_data_type.v_model,
        }
        if self.w_id.v_model in self.model.ids:
            self.model.update_constraint(**kwargs)
        else:
            self.model.add_constraint(**kwargs)

        # close the dialog
        self.value = False

    def open_new(self, *args) -> None:
        """open new dialog with default values."""
        # reset the alert
        self.w_alert.reset()

        self.fill(*[None] * 7)

        # open the dialog
        self.value = True

    def cancel(self, *args) -> None:
        """close and do nothing."""
        self.value = False

    def theme_change(self, *args) -> None:
        """edit the list of default theme."""
        default_layers = self._CONSTRAINTS[
            self._CONSTRAINTS.subtheme == self.w_theme.v_model
        ]
        default_layers = default_layers.layer_id.unique().tolist()
        self.w_name.items = [cm.layers[ly].name for ly in default_layers]
        self.w_name.v_model = next(iter(self.w_name.items), "")

    def name_change(self, *args) -> None:
        """if the selected layer is from the combo box items, select all the default informations."""
        if not self.w_name.v_model:
            self.fill("custom", *[""] * 6)
            return

        if self.w_name.v_model not in self.w_name.items:
            return

        # get the information from the dataframe
        layer_id = next(
            k for k, ly in cm.layers.items() if ly.name == self.w_name.v_model
        )
        # TODO: why this is called constraints?
        benefit = self._CONSTRAINTS[self._CONSTRAINTS.layer_id == layer_id].iloc[0]

        # fill the different widgets
        self.w_id.v_model = layer_id
        self.w_asset.v_model = benefit.gee_asset
        # add the asset as default value so it won't be lost if the user change it,, do this manually otherewise it will take sometime
        header = {"header": cm.default_asset_header}
        default_asset_item = [header, benefit.gee_asset]
        if header not in self.w_asset.items:
            self.w_asset.items = default_asset_item + self.w_asset.items

        self.w_desc.v_model = cm.layers[layer_id].detail
        self.w_unit.v_model = benefit.unit

    def fill(
        self,
        theme: str,
        name: str,
        id: str,
        asset: str,
        desc: str,
        unit: str,
        data_type: str,
    ) -> None:
        """fill the dialog with data from the link."""
        self.w_theme.v_model = theme
        self.w_name.v_model = name
        self.w_id.v_model = id
        self.w_asset.v_model = asset
        self.w_desc.v_model = desc
        self.w_unit.v_model = unit
        self.w_data_type.v_model = data_type
