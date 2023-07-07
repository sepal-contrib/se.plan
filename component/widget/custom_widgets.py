from typing import Union

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from traitlets import Int, link

from component.model import BenefitModel, ConstraintModel, CostModel

from .benefit_dialog import BenefitDialog
from .constraint_dialog import ConstraintDialog
from .cost_dialog import CostDialog


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
        model: Union[BenefitModel, ConstraintModel, CostModel],
        dialog: Union[ConstraintDialog, CostDialog, BenefitDialog],
    ) -> None:
        super().__init__()

        self.model = model
        self.dialog = dialog

        if isinstance(model, BenefitModel):
            name = "benefit"
        elif isinstance(model, ConstraintModel):
            name = "constraint"
        elif isinstance(model, CostModel):
            name = "cost"

        self.w_new = sw.Btn(
            f"New {name}", "fa-solid fa-plus", small=True, type_="success"
        )

        # add js behaviour
        self.w_new.on_event("click", self.open_new_dialog)

        self.children = [
            sw.Spacer(),
            sw.Divider(vertical=True, class_="mr-2"),
            self.w_new,
        ]

    @sd.switch("loading", on_widgets=["dialog"])
    def open_new_dialog(self, *args) -> None:
        """open the new benefit dialog."""
        self.dialog.open_new()


class Tabs(sw.Card):
    current = Int(0).tag(sync=True)

    def __init__(self, titles, content, **kwargs):
        self.background_color = "primary"
        self.dark = True

        self.tabs = [
            sw.Tabs(
                v_model=self.current,
                children=[
                    sw.Tab(children=[title], key=key)
                    for key, title in enumerate(titles)
                ],
            )
        ]

        self.content = [
            sw.TabsItems(
                v_model=self.current,
                children=[
                    sw.TabItem(children=[content], key=key)
                    for key, content in enumerate(content)
                ],
            )
        ]

        self.children = self.tabs + self.content

        link((self.tabs[0], "v_model"), (self.content[0], "v_model"))

        super().__init__(**kwargs)
