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


class ToolBar(sw.Toolbar):
    def __init__(
        self,
        model: Union[PriorityModel, ConstraintModel, CostModel],
        dialog: Union[ConstraintDialog, CostDialog, PriorityDialog],
    ) -> None:
        super().__init__()

        self.model = model
        self.dialog = dialog

        if isinstance(model, PriorityModel):
            name = "priority"
        elif isinstance(model, ConstraintModel):
            name = "constraint"
        elif isinstance(model, CostModel):
            name = "cost"

        self.w_new = sw.Btn(
            f"New {name}", "fa-solid fa-plus", small=True, type_="success"
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
