from sepal_ui import sepalwidgets as sw
from traitlets import Unicode
import pandas as pd

from component.message import cm
from component import new_model as cmod
from component import parameter as cp


class PriorityDialog(sw.Dialog):

    name = Unicode("").tag(sync=True)
    id = Unicode("").tag(sync=True)
    theme = Unicode("").tag(sync=True)
    asset = Unicode("").tag(sync=True)
    desc = Unicode("").tag(sync=True)
    unit = Unicode("").tag(sync=True)

    _PRIORITIES = pd.read_csv(cp.layer_list)
    _PRIORITIES = _PRIORITIES[_PRIORITIES.theme == "benefit"]

    def __init__(self, model: cmod.PriorityModel):

        # save the model as a member
        self.model = model

        # create the title
        w_title = sw.CardTitle(children=[cm.priority_dialog.title.capitalize()])

        # create the content
        w_theme = sw.Select(
            label=cm.priority_dialog.theme,
            items=[{"text": v, "value": k} for k, v in cm.subtheme.items()],
            class_="on-dialog",
        )
        w_name = sw.Combobox(
            label=cm.priority_dialog.name,
            items=[
                cm.layers[ly].name for ly in self._PRIORITIES.layer_id.unique().tolist()
            ],
        )
        w_asset = sw.AssetSelect()
        w_desc = sw.Textarea(label=cm.priority_dialog.desc)
        w_unit = sw.TextField(label=cm.priority_dialog.unit)
        w_content = sw.CardText(children=[w_theme, w_name, w_asset, w_desc, w_unit])

        # create the actions
        self.w_validate = sw.Btn(
            cm.priority_dialog.validate, "fa-solid fa-check", type_="success"
        )
        self.w_cancel = sw.Btn(
            cm.priority_dialog.cancel, "fa-solid fa-times", type_="error"
        )
        w_actions = sw.CardActions(
            children=[sw.Spacer(), self.w_validate, self.w_cancel]
        )

        card = sw.Card(children=[w_title, w_content, w_actions])

        super().__init__(
            persistent=True,
            value=False,
            max_width="700px",
            children=[card],
        )

        # add JS behaviour
        self.w_validate.on_event("click", self.validate)
        self.w_cancel.on_event("click", self.cancel)

    def validate(self, *args) -> None:
        """save the layer in the model (update or add)"""

        pass

    def cancel(self, *args) -> None:
        """close and do nothing"""
        self.value = False
