import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

from component import parameter as cp
from component.message import cm
from component.model.benefit_model import BenefitModel
from component.widget import custom_widgets as cw
from component.widget.benefit_dialog import BenefitDialog


class BenefitRow(sw.Html):
    _DEFAULT_THEMES = pd.read_csv(cp.layer_list).layer_id

    def __init__(
        self, model: BenefitModel, layer_id: str, dialog: BenefitDialog, **kwargs
    ) -> None:
        self.tag = "tr"
        self.attributes = {"layer_id": layer_id}

        super().__init__()

        # get the model as a member
        self.model = model
        self.dialog = dialog

        idx = model.get_index(id=layer_id)

        # extract information from the model
        self.name = self.model.names[idx]
        self.layer_id = self.model.ids[idx]
        self.theme = self.model.themes[idx]
        self.weight = self.model.weights[idx]

        self.update_view()

    def update_view(self):
        """Create the view of the widget based on the model."""
        # create the crud interface
        self.edit_btn = cw.TableIcon("fa-solid fa-pencil", self.layer_id)
        self.delete_btn = cw.TableIcon("fa-solid fa-trash-can", self.layer_id)
        self.edit_btn.class_list.add("mr-2")

        # create the checkbox_list
        self.check_list = []
        for i in range(5):
            attr = {"data-label": self.layer_id, "data-val": i}
            check = sw.Checkbox(attributes=attr, v_model=i == self.weight)
            self.check_list.append(check)

        td_list = [
            sw.Html(tag="td", children=[self.edit_btn, self.delete_btn]),
            sw.Html(tag="td", children=[cm.subtheme[self.theme]]),
            sw.Html(tag="td", children=[self.name]),
            *[sw.Html(tag="td", children=[e]) for e in self.check_list],
        ]

        self.children = td_list

        # add js behaviour
        [e.observe(self.on_check_change, "v_model") for e in self.check_list]
        self.delete_btn.on_event("click", self.on_delete)
        self.edit_btn.on_event("click", self.on_edit)

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

        return

    def on_delete(self, widget, data, event):
        """remove the line from the model and trigger table update."""
        self.model.remove_benefit(widget.attributes["data-layer"])

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
        self.dialog.value = True