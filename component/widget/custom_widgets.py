from typing import Union

import ipyleaflet as ipl
import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from traitlets import Int, link, observe

from component.message import cm
from component.model import BenefitModel, ConstraintModel, CostModel, SeplanAoi
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

    @sd.catch_errors(debug=True)
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


class CustomDrawerItem(sw.DrawerItem):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.viz = False

    @observe("alert")
    def add_notif(self, change: dict) -> None:
        """Add a notification alert to drawer."""
        if change["new"]:
            self.viz = True
            if self.alert_badge not in self.children:
                new_children = self.children[:]
                new_children.append(self.alert_badge)
                self.children = new_children
        else:
            self.viz = False
            self.remove_notif()

        return


def Legend() -> ipl.WidgetControl:
    """Create a legend for the map.

    Colors of the table will come from a css simple file located in fronted.
    """
    style = sw.Html(
        tag="style",
        children=[
            """
            .legend {
                height: 25px;
                background-color: #353535;
                background-image:
                    linear-gradient(
                    to right, 
                    #353535,
                    #353535 16.66%,
                    #edf8fb 16.66%,
                    #66c2a4,
                    #006d2c
                    );
            }

            .td_title {
                text-align:center !important;
                font-size: 14px !important;
                height: auto !important;
            }

            .td_legend {
                padding: 0px !important;
                height: auto !important;
            }

            .td_label {
                width: 16.66%;
                font-size: 12px !important;
                line-height: 18px !important;
                text-align:center !important;
                height: auto !important;
            }
            """
        ],
    )

    title = sw.Html(
        tag="td",
        class_="td_title",
        attributes={"colspan": 6},
        children=[sw.Html(tag="div", children="Restoration suitability index")],
    )

    legend_bar = sw.Html(
        tag="td",
        class_="td_legend",
        attributes={"colspan": 6},
        children=[sw.Html(tag="div", class_="legend")],
    )

    legend_names = {
        "nodata": cm.map.legend.class_.nodata,
        "vlow": cm.map.legend.class_.vlow,
        "low": cm.map.legend.class_.low,
        "medium": cm.map.legend.class_.medium,
        "high": cm.map.legend.class_.high,
        "vhigh": cm.map.legend.class_.vhigh,
    }

    legend_label = [
        sw.Html(tag="td", class_="td_label", children=[name])
        for name in legend_names.values()
    ]

    legend = sw.SimpleTable(
        style_="width:450px; background-color: transparent;",
        class_="pa-0 ma-0",
        children=[
            style,
            sw.Html(tag="tr", children=[title]),
            sw.Html(tag="tr", children=[legend_bar]),
            sw.Html(tag="tr", children=legend_label),
        ],
    )
    # return legend

    return ipl.WidgetControl(
        widget=legend,
        position="bottomright",
        transparent_bg=True,
    )
