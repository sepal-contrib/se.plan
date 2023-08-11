from typing import Union

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from traitlets import Int, link

from component.message import cm
from component.model import BenefitModel, ConstraintModel, CostModel
from component.model.aoi_model import SeplanAoi
from component.scripts.seplan import Seplan
from component.widget.alert_state import Alert

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
        seplan_aoi: SeplanAoi,
        alert: Alert,
    ) -> None:
        super().__init__()

        self.model = model
        self.dialog = dialog
        self.alert = alert
        self.seplan_aoi = seplan_aoi

        if isinstance(model, BenefitModel):
            name = "benefit"
        elif isinstance(model, ConstraintModel):
            name = "constraint"
        elif isinstance(model, CostModel):
            name = "cost"

        self.w_new = sw.Btn(f"New {name}", "mdi-plus", small=True, type_="success")

        # add js behaviour
        self.w_new.on_event("click", self.open_new_dialog)

        self.children = [
            sw.Spacer(),
            sw.Divider(vertical=True, class_="mr-2"),
            self.w_new,
        ]

    @sd.catch_errors()
    def open_new_dialog(self, *args) -> None:
        """open the new benefit dialog."""
        # Avoid opening if there is not a valid AOI when adding a constraint
        if (
            isinstance(self.model, ConstraintModel)
            and not self.seplan_aoi.feature_collection
        ):
            raise Exception(cm.questionnaire.error.no_aoi)

        self.dialog.open_new()


class DashToolBar(sw.Toolbar):
    def __init__(self, model: Seplan) -> None:
        super().__init__()

        self.model = model

        self.btn_download = sw.Btn(
            gliph="mdi-download",
            icon=True,
            color="primary",
        ).set_tooltip(
            cm.dashboard.toolbar.btn.download.tooltip, right=True, max_width="200px"
        )

        self.btn_dashboard = sw.Btn(
            cm.dashboard.toolbar.btn.compute.title, class_="ma-2"
        )

        self.children = [
            self.btn_download.with_tooltip,
            sw.Spacer(),
            sw.Divider(vertical=True, class_="mr-2"),
            self.btn_dashboard,
        ]


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
