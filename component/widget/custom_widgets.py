from typing import Literal, Union

from component.widget.expression import ExpressionBtn
import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from traitlets import Int, Unicode, link, observe

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

        children = [sw.Spacer()]

        if isinstance(model, BenefitModel):
            children.append(ExpressionBtn(model))

        self.children = children + [
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


class CustomDrawerItem(sw.DrawerItem):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.attributes = {"id": kwargs["card"]}

        # Only hide the drawers that are not the main ones
        if self.attributes["id"] not in (["recipe_tile", "about_tile"]):
            self.viz = False

    @observe("alert")
    def add_notif(self, change: dict) -> None:
        """Add a notification alert to drawer."""
        if self.attributes["id"] in (["recipe_tile", "about_tile"]):
            return

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


class CustomNavDrawer(sw.NavDrawer):
    active_drawer = Unicode("").tag(sync=True)

    def __init__(self, *args, app_model=None, **kwargs):
        self.app_model = app_model

        super().__init__(*args, **kwargs)

        link((self, "active_drawer"), (self.app_model, "active_drawer"))

    def _on_item_click(self, change: dict):
        """Deactivate all the other items when on of the is activated."""
        if change["new"] is False:
            return self

        self.active_drawer = change["owner"].attributes["id"]

        # reset all others states
        [setattr(i, "input_value", False) for i in self.items if i != change["owner"]]

        return self


class CustomAppBar(sw.AppBar):

    save_recipe_btn = sw.Btn(
        gliph="mdi-content-save",
        icon=True,
    )
    save_recipe_btn.v_icon.left = False

    recipe_holder = sw.Flex(
        attributes={"id": "recipe_holder"},
        class_="d-inline-flex justify-end",
        style_="align-items: center;",
        children=[
            sw.Html(
                tag="span",
                class_="text--secondary mr-1",
                attributes={"id": "recipe_name"},
            ),
            sw.Html(
                tag="span",
                class_="font-weight-thin font-italic text-lowercase",
                attributes={"id": "new_changes"},
            ),
            save_recipe_btn,
        ],
    )

    def update_recipe(
        self, element: Literal["recipe_name", "new_changes"], value: str = ""
    ) -> None:
        """Update the recipe name and state in the app bar."""
        if not value:
            return

        if not self.get_children(attr="id", value="recipe_holder"):
            self.children = self.children[:3] + [self.recipe_holder] + self.children[3:]

        if element == "new_changes":
            value = cm.app.recipe_state[value]

        self.get_children(attr="id", value=element)[0].children = value


class CustomApp(sw.App):
    def __init__(self, app_model, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app_model = app_model
        self.app_model.observe(self.update_recipe_state, "recipe_name")
        self.app_model.observe(self.update_recipe_state, "new_changes")

        self.appBar.save_recipe_btn.on_event("click", self.save_recipe)

    def save_recipe(self, *_):
        """Save the recipe in the app model."""
        self.app_model.on_save += 1

    def update_recipe_state(self, change):
        """Update the recipe state in the app bar."""
        print("update_recipe_state")

        if not change["new"]:
            change["new"] = ""

        if change["name"] == "new_changes":
            change["new"] = "unsaved" if change["new"] else "saved"
        else:
            change["new"] = change["new"].split("/")[-1].replace(".json", "")

        self.appBar.update_recipe(element=change["name"], value=change["new"])
