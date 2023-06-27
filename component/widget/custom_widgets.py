from typing import Union

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

from component.model import ConstraintModel, CostModel, PriorityModel
from component.widget.constraint.constraint_dialog import ConstraintDialog
from component.widget.cost.cost_dialog import CostDialog
from component.widget.priority.priority_dialog import PriorityDialog


class TableIcon(sw.Icon):
    """A simple icon to be used in a table."""

    def __init__(self, gliph: str, name: str):
        super().__init__(
            children=[gliph],
            icon=True,
            small=True,
            attributes={"data-layer": name},
            style_="font: var(--fa-font-solid);",
        )


class SimpleRangeSlider(sw.RangeSlider):
    def __init__(self, **kwargs) -> None:
        """Simple Slider is a simplified slider that can be center alined in table.

        The normal vuetify slider is included html placeholder for the thumbs and the messages (errors and hints). This is preventing anyone from center-aligning them in a table. This class is behaving exactly like a regular Slider but embed extra css class to prevent the display of these sections. any hints or message won't be displayed.
        """
        super().__init__(**kwargs)
        self.class_list.add("v-no-messages")


class ToolBar(sw.Toolbar):
    def __init__(
        self,
        model: Union[PriorityModel, ConstraintModel, CostModel],
        dialog: Union[ConstraintDialog, CostDialog, PriorityDialog],
    ) -> None:
        super().__init__()

        self.model = model
        self.dialog = dialog

        self.w_new = sw.Btn(
            "New Priority", "fa-solid fa-plus", small=True, type_="success"
        )
        self.w_validate = sw.Btn(
            "validate", "fa-solid fa-check", small=True, class_="ml-1"
        )

        # add js behaviour
        self.w_new.on_event("click", self.open_new_dialog)
        self.w_validate.on_event("click", self.validate)

        self.children = [
            sw.Spacer(),
            sw.Divider(vertical=True, class_="mr-2"),
            self.w_new,
            self.w_validate,
        ]

    @sd.switch("loading", on_widgets=["dialog"])
    def open_new_dialog(self, *args) -> None:
        """open the new priority dialog."""
        self.dialog.open_new()

    def validate(self, *args):
        self.model.validated += 1
