"""Custom alert component to inform the user the state of the building process."""

from typing import Literal

import sepal_ui.sepalwidgets as sw

from component.message import cm


class AlertState(sw.Alert):
    """Custom alert component to inform the user the state of the building process."""

    def update_state(self, component_id, state) -> None:
        """Mutate and set new message by replacing."""
        print(f"updating {component_id} to {state}")

        message_component = next(
            iter(self.get_children(attr="id", value=component_id)), None
        )

        if not message_component:
            message_component = TaskMsg(component_id)
            self.append_msg(message_component)

        message_component.set_state(state)


class TaskMsg(sw.Flex):
    def __init__(
        self,
        component_id: Literal["aoi", "questionnaire", "map", "dashboard"],
    ) -> None:
        super().__init__()
        self.attributes = {"id": component_id}
        self.class_ = "d-flex"
        self.icon = sw.Icon(children=["mdi-circle"], color="info")

        self.children = ["", sw.Spacer(), self.icon]

    def set_state(self, state: Literal["building", "done", "error"]) -> None:
        """Sets a state (color) to the icon."""
        if state == "building":
            self.icon.children = ["mdi-wrench"]
        elif state == "done":
            self.icon.children = ["mdi-checkbox-marked"]
        elif state == "waiting":
            self.icon.children = ["mdi-clock-alert-outline"]

        # Get the corresponding message for this component and state
        msg = cm.recipe.states[self.attributes["id"]][state]

        self.children = [msg] + self.children[1:]
