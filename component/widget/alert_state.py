"""Custom alert component to inform the user the state of the building process."""

from typing import Literal

import sepal_ui.sepalwidgets as sw
from traitlets import Dict, observe

from component.message import cm


class AlertState(sw.Alert):
    """Custom alert component to inform the user the state of the building process."""

    # Define traits
    build_state = Dict(
        {
            "aoi": "waiting",
            "questionnaire": "waiting",
            "map": "waiting",
            "dashboard": "waiting",
            "load": "waiting",
        }
    ).tag(sync=True)

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

    @observe("build_state")
    def update_messages(self, change):
        """Update custom alert messages based on the UI build state.

        This method is called every time the build_state of the recipe changes,
        and it changes everytime the build state ("building", "done", "error")
        of one of the components changes.

        """
        for component_id, state in change["new"].items():
            self.update_state(component_id, state)

    def set_state(
        self,
        component: Literal["aoi", "questionnaire", "map", "dashboard", "load"],
        value: Literal["building", "done", "waiting"],
    ):
        """Set the done status of a component to True or False."""
        tmp_state = self.build_state.copy()
        tmp_state[component] = value
        self.build_state = tmp_state


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
