"""Custom alert component to inform the user the state of the building process after selecting a new or loading an existing recipe."""

from typing import Literal

import sepal_ui.sepalwidgets as sw
from ipyvuetify import Btn

from component.message import cm

default_state = {
    "new": {
        "aoi": "waiting",
        "questionnaire": "waiting",
        "map": "waiting",
        "dashboard": "waiting",
    },
    "load": {
        "aoi": "waiting",
        "questionnaire": "waiting",
        "map": "waiting",
        "dashboard": "waiting",
    },
    "reset": {
        "aoi": "waiting",
        "questionnaire": "waiting",
        "map": "waiting",
        "dashboard": "waiting",
    },
}

icons = {
    "building": "mdi-wrench",
    "done": "mdi-checkbox-marked-circle",
    "waiting": "mdi-clock-alert",
}


class Alert(sw.Alert):
    def __init__(self) -> None:
        """Set some default values."""
        self.style_ = "margin: 0 !important;"
        super().__init__()


class AlertState(Alert):
    """Custom alert component to inform the user the state of the building process."""

    def set_state(
        self,
        type_: Literal["new", "load"],
        component: Literal["aoi", "questionnaire", "map", "dashboard", "load", "all"],
        state: Literal["building", "done", "waiting"],
    ):
        """Set a given state to a component on the given type_ (step)."""
        if component == "all":
            # get all the components for this type_
            message_components = self.get_children(attr="type_", value=type_)

            # if there are not components, create them
            if not message_components:
                message_components = [
                    TaskMsg(type_, component)
                    for component in default_state[type_].keys()
                ]
                [
                    self.append_msg(message_component)
                    for message_component in message_components
                ]

            # set the state to all the components
            [
                message_component.set_state(state)
                for message_component in message_components
            ]

        else:
            message_component = next(
                iter(self.get_children(attr="id", value=(type_ + component))), None
            )

            if not message_component:
                message_component = TaskMsg(type_, component)
                self.append_msg(message_component)

            message_component.set_state(state)


class TaskMsg(sw.Flex):
    def __init__(
        self,
        type_: Literal["new", "load", "save"],
        component_id: Literal["aoi", "questionnaire", "map", "dashboard"],
    ) -> None:
        super().__init__()
        self.type_ = type_
        self.component_id = component_id
        self.attributes = {"id": type_ + component_id, "type_": type_}
        self.class_ = "d-flex"
        self.icon = sw.Icon(children=["mdi-circle"], color="info")

        self.children = ["", sw.Spacer(), self.icon]

    def set_state(self, state: Literal["building", "done", "error"]) -> None:
        """Sets a state (color) to the icon."""
        self.icon.children = [icons[state]]

        # Get the corresponding message for this component and state
        msg = cm.recipe.states[self.type_][self.component_id][state]

        self.children = [msg] + self.children[1:]


class AlertDialog(sw.Dialog):
    def __init__(self, w_alert: AlertState):
        self.max_width = 650
        self.persistent = True
        super().__init__()

        self.v_model = False
        self.w_alert = w_alert

        btn_close = Btn(
            color="primary",
            block=True,
            children=["Close"],
        )
        self.children = [
            sw.Card(
                # class_="pa-2",
                children=[
                    self.w_alert,
                    sw.CardActions(children=[btn_close], class_="pa-0 pt-2"),
                ],
            )
        ]
        btn_close.on_event("click", lambda *_: setattr(self, "v_model", False))
        self.w_alert.observe(self.open_dialog, "children")

    def open_dialog(self, change):
        """Opens the dialog when there's a change in the alert chilndren state."""
        if change["new"] != [""]:
            self.v_model = True
