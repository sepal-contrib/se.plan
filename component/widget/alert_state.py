"""Custom alert component to inform the user the state of the building process after selecting a new or loading an existing recipe."""


from typing import Literal

import sepal_ui.sepalwidgets as sw
from ipyvuetify import Btn
from traitlets import Dict, observe

from component.message import cm

Types = Literal["create", "load", "save"]
Component = Literal["aoi", "questionnaire", "map", "dashboard", "load"]

# Default trait values
default_state = {
    "new": {
        "aoi": "waiting",
        "questionnaire": "waiting",
        "map": "waiting",
        "dashboard": "waiting",
    },
    "load": {"all": "waiting"},
    "save": {"all": "waiting"},
}


class Alert(sw.Alert):
    def __init__(self) -> None:
        """Set some default values."""
        self.style_ = "margin: 0 !important;"
        super().__init__()


class AlertState(Alert):
    """Custom alert component to inform the user the state of the building process."""

    # Define traits
    new = Dict(default_state["new"]).tag(sync=True)

    load = Dict(default_state["load"]).tag(sync=True)

    save = Dict(default_state["save"]).tag(sync=True)

    def reset(self):
        """reset traits and reset alert."""
        self.new = default_state["new"]
        self.load = default_state["load"]
        self.save = default_state["save"]
        super().reset()

    def update_state(self, type_, component_id, state) -> None:
        """Mutate and set new message by replacing."""
        # Get the corresponding "line_message" component
        message_component = next(
            iter(self.get_children(attr="id", value=(type_ + component_id))), None
        )

        if not message_component:
            message_component = TaskMsg(type_, component_id)
            self.append_msg(message_component)

        message_component.set_state(state)

    @observe("new", "load", "save")
    def update_messages(self, change):
        """Update custom alert messages based on the UI type [new, load, save] state.

        This method is called every time the traits of the class changes.
        It will update the message of the corresponding "line_component".

        """
        for component_id, state in change["new"].items():
            print(change["name"], component_id, state)
            self.update_state(change["name"], component_id, state)

    def set_state(
        self,
        type_: Types,
        component,
        value: Literal["building", "done", "waiting"],
    ):
        """Set the done status of a component."""
        state_trait = {
            "new": self.new,
            "load": self.load,
            "save": self.save,
        }

        tmp_state = state_trait[type_].copy()
        tmp_state[component] = value

        if type_ == "new":
            self.new = tmp_state
        elif type_ == "load":
            self.load = tmp_state
        elif type_ == "save":
            self.save = tmp_state


class TaskMsg(sw.Flex):
    def __init__(
        self,
        type_: Literal["new", "load", "save"],
        component_id: Literal["aoi", "questionnaire", "map", "dashboard"],
    ) -> None:
        super().__init__()
        self.type_ = type_
        self.component_id = component_id
        self.attributes = {"id": type_ + component_id}
        self.class_ = "d-flex"
        self.icon = sw.Icon(children=["mdi-circle"], color="info")

        self.children = ["", sw.Spacer(), self.icon]

    def set_state(self, state: Literal["building", "done", "error"]) -> None:
        """Sets a state (color) to the icon."""
        icons = {
            "building": "mdi-wrench",
            "done": "mdi-checkbox-marked-circle",
            "waiting": "mdi-clock-alert",
        }

        self.icon.children = [icons[state]]

        # Get the corresponding message for this component and state
        msg = cm.recipe.states[self.type_][self.component_id][state]

        self.children = [msg] + self.children[1:]


class AlertDialog(sw.Dialog):
    def __init__(self, w_alert: AlertState):
        self.max_width = 650
        super().__init__()

        self.v_model = False
        self.w_alert = w_alert

        btn_close = Btn(
            block=True,
            children=["Close"],
        )
        self.children = [
            sw.Card(
                children=[
                    self.w_alert,
                    sw.CardActions(children=[btn_close]),
                ]
            )
        ]
        btn_close.on_event("click", lambda *_: setattr(self, "v_model", False))
        self.w_alert.observe(self.open_dialog, "children")

    def open_dialog(self, change):
        """Opens the dialog when there's a change in the alert chilndren state."""
        if change["new"] != [""]:
            self.v_model = True
