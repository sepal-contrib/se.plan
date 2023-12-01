import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

from component import parameter as cp
from component.message import cm
from component.model.aoi_model import SeplanAoi
from component.model.benefit_model import BenefitModel
from component.scripts.seplan import asset_to_image
from component.widget import custom_widgets as cw
from component.widget.alert_state import Alert
from component.widget.benefit_dialog import BenefitDialog

from .preview_map_dialog import PreviewMapDialog


class BenefitRow(sw.Html):
    _DEFAULT_THEMES = pd.read_csv(cp.layer_list).layer_id

    def __init__(
        self,
        model: BenefitModel,
        layer_id: str,
        dialog: BenefitDialog,
        aoi_model: SeplanAoi,
        alert: Alert,
        preview_map: PreviewMapDialog,
    ) -> None:
        self.tag = "tr"
        self.layer_id = layer_id
        self.attributes = {"layer_id": layer_id}
        super().__init__()

        # get the model as a member
        self.model = model
        self.dialog = dialog
        self.preview_map = preview_map
        self.aoi_model = aoi_model
        self.alert = alert

        self.get_model_data()

        # create the crud interface
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

        # extract information from the model
        self.name = self.model.names[idx]
        self.asset = self.model.assets[idx]
        self.theme = self.model.themes[idx]
        self.weight = self.model.weights[idx]

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

        # create the checkbox_list
        self.check_list = []
        for i in range(5):
            attr = {"data-label": self.layer_id, "data-val": i}
            check = sw.Checkbox(attributes=attr, v_model=i == self.weight)
            self.check_list.append(check)

        td_list = [
            sw.Html(
                tag="td", children=[self.edit_btn, self.delete_btn, self.show_map_btn]
            ),
            sw.Html(tag="td", children=[cm.subtheme[self.theme]]),
            sw.Html(tag="td", children=[self.name]),
            *[sw.Html(tag="td", children=[e]) for e in self.check_list],
        ]

        self.children = td_list

        # add js behaviour
        [e.observe(self.on_check_change, "v_model") for e in self.check_list]

    def update_value(self):
        """Update the value of the model."""
        # check which checkbox is checked and get its value
        checked = [check for check in self.check_list if check.v_model]
        self.weight = checked[0].attributes["data-val"]

        self.model.update_value(self.layer_id, self.weight)

        self.get_model_data()

    def on_check_change(self, change):
        # if checkbox is unique and change == false recheck
        if change["new"] is False:
            unique = True
            for check in self.check_list:
                if check.v_model is True:
                    unique = False
                    break

            change["owner"].v_model = unique

        else:
            # uncheck all the others in the line
            for check in self.check_list:
                if check != change["owner"]:
                    check.v_model = False

        self.update_value()

    @sd.catch_errors()
    def on_delete(self, widget, *_):
        """remove the line from the model and trigger table update."""
        if widget.attributes["data-layer"] in cp.mandatory_layers["benefit"]:
            raise Exception(cm.questionnaire.error.mandatory_layer)

        # You cannot delete the last layer
        if len(self.model.ids) == 1:
            raise Exception(cm.questionnaire.error.last_layer)

        self.model.remove(widget.attributes["data-layer"])

    @sd.switch("loading", on_widgets=["dialog"])
    def on_edit(self, widget, data, event):
        """open the dialog with the data contained in the model."""
        idx = self.model.get_index(widget.attributes["data-layer"])

        self.dialog.fill(
            theme=self.model.themes[idx],
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
            unit=self.model.units[idx],
        )
        # clean any previous errors
        self.dialog.w_alert.reset()
        self.dialog.open_dialog()
