from pathlib import Path
from typing import Literal, Union

from component.model.recipe import Recipe
from component.scripts import validation
from component.widget.expression import ExpressionBtn
import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from component import widget as cw


from sepal_ui.frontend.styles import get_theme
from traitlets import Bool, Int, Unicode, directional_link, link, observe
from sepal_ui.sepalwidgets.widget import Markdown
import ipyvuetify as v
import component.parameter as cp


from component.message import cm
from component.model import BenefitModel, ConstraintModel, CostModel, SeplanAoi
from component.scripts.seplan import Seplan
from component.widget.alert_state import Alert
from component.widget.preview_theme_btn import PreviewThemeBtn
from component.widget.buttons import IconBtn, TextBtn

from .benefit_dialog import BenefitDialog
from .constraint_dialog import ConstraintDialog
from .cost_dialog import CostDialog


class RecipeInput(sw.FileInput):

    load_recipe_path = Unicode(None, allow_none=True).tag(sync=True)
    valid = Bool(False).tag(sync=True)

    def __init__(self, main_recipe: Recipe = None, **kwargs):
        super().__init__(".json", folder=cp.result_dir, root=cp.result_dir, **kwargs)

        self.text_field_msg = self.children[-1]
        self.observe(self.validate_input, "v_model")

        loading_button = self.children[2].v_slots[0]["children"]
        loading_button.small = True
        self.reload.small = True

        if main_recipe:
            main_recipe.observe(self.set_default_recipe, "recipe_session_path")
            loading_button.disabled = True
            self.reload.disabled = True

    def set_default_recipe(self, change):
        """Set the default recipe."""

        recipe_session_path = change["new"]

        self.select_file(recipe_session_path)

    def validate_input(self, change):
        """Validate the recipe file."""
        if not change["new"]:
            return

        self.valid = False

        # Reset any previous error messages
        self.text_field_msg.error_messages = []

        # Validate the recipe file and show errors if there are
        self.load_recipe_path = validation.validate_recipe(
            change["new"], self.text_field_msg
        )

        self.valid = bool(self.load_recipe_path)


class TableIcon(sw.Icon):
    """A simple icon to be used in a table."""

    def __init__(self, gliph: str, name: str, **kwargs: dict) -> None:
        small = kwargs.pop("small", True)
        kwargs["x_small"] = kwargs.pop("x_small", False)
        super().__init__(
            children=[gliph],
            icon=True,
            small=small,
            attributes={"data-layer": name},
            style_="font: var(--fa-font-solid);",
            **kwargs,
        )


class ToolBar(sw.Toolbar):
    def __init__(
        self,
        model: Union[BenefitModel, ConstraintModel, CostModel],
        dialog: Union[ConstraintDialog, CostDialog, BenefitDialog],
        seplan_aoi: SeplanAoi,
        alert: Alert,
        preview_theme_map_btn: PreviewThemeBtn = "",
    ) -> None:
        super().__init__()

        self.model = model
        self.dialog = dialog
        self.alert = alert
        self.seplan_aoi = seplan_aoi
        self.elevation = 0
        self.color = "accent"

        if isinstance(model, BenefitModel):
            name = "benefit"
        elif isinstance(model, ConstraintModel):
            name = "constraint"
        elif isinstance(model, CostModel):
            name = "cost"

        self.w_new = TextBtn(f"New {name}", gliph="mdi-plus", type_="success")

        # add js behaviour
        self.w_new.on_event("click", self.open_new_dialog)

        children = [sw.Spacer(), preview_theme_map_btn]

        if isinstance(model, BenefitModel):
            children.append(ExpressionBtn(model))

        self.children = children + [
            sw.Divider(vertical=True, class_="ml-1 mr-2"),
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


class DashToolbar(sw.Toolbar):
    def __init__(self, model: Seplan, alert: Alert = None) -> None:
        super().__init__()

        alert = alert or Alert()

        self.height = "48px"
        self.model = model
        self.elevation = 0
        self.color = "accent"

        self.btn_download = IconBtn(
            gliph="fa-solid fa-circle-down",
        ).set_tooltip(
            cm.dashboard.toolbar.btn.download.tooltip, right=True, max_width="200px"
        )
        self.btn_compare = IconBtn(gliph="mdi-compare").set_tooltip(
            cm.dashboard.toolbar.btn.compare.tooltip, right=True, max_width="200px"
        )

        self.compare_dialog = cw.CompareScenariosDialog(type_="chart", alert=alert)

        self.btn_compare.on_event("click", lambda *_: self.compare_dialog.open_dialog())
        self.btn_dashboard = TextBtn(cm.dashboard.toolbar.btn.compute.title)

        self.children = [
            self.btn_download.with_tooltip,
            sw.Spacer(),
            self.btn_compare.with_tooltip,
            sw.Divider(vertical=True, class_="mr-2"),
            self.btn_dashboard,
            # Dialogs
            self.compare_dialog,
        ]


class Tabs(sw.Card):
    current = Int(0).tag(sync=True)

    def __init__(self, titles, content, **kwargs):
        self.background_color = "primary"

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

        self.observe(self.add_notif, "alert")

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

    save_recipe_btn = IconBtn(gliph="mdi-content-save")
    save_recipe_btn.color = "#f3f3f3"
    save_recipe_btn.v_icon.left = False

    recipe_holder = sw.Flex(
        attributes={"id": "recipe_holder"},
        class_="d-inline-flex justify-end",
        style_="align-items: center;",
        children=[
            sw.Html(
                tag="span",
                class_="mr-1 white--text",
                attributes={"id": "recipe_name"},
            ),
            sw.Html(
                tag="span",
                class_="font-weight-thin font-italic text-lowercase mr-2 white--text",
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

        if not change["new"]:
            change["new"] = ""

        if change["name"] == "new_changes":
            change["new"] = "unsaved" if change["new"] else "saved"
        else:
            change["new"] = change["new"].split("/")[-1].replace(".json", "")

        self.appBar.update_recipe(element=change["name"], value=change["new"])


class CustomTileAbout(sw.Tile):
    def __init__(self, pathname: Union[str, Path], **kwargs) -> None:
        """Create an about tile using a .md file.

        This tile will have the "about_widget" id and "About" title.

        Args:
            pathname: the path to the .md file
        """

        text = Path(pathname).read_text()

        # get current stored theme
        theme = get_theme()

        # Search any url in the text and look for the dark/light theme
        text = (
            text.replace("/light/", "/dark/")
            if theme == "dark"
            else text.replace("/dark/", "/light/")
        )

        content = Markdown(text)

        update_script = UpdateImages(dark=True)
        super().__init__("about_tile", "About", inputs=[content, update_script])

        directional_link((v.theme, "dark"), (update_script, "dark"))


class UpdateImages(v.VuetifyTemplate):
    """Update the image source when the theme changes."""

    dark = Bool(v.theme.dark, allow_none=True).tag(sync=True)
    template = Unicode(
        """
        <script class='sepal-ui-script'>
            {
                methods: {
                    jupyter_updateImageSources() {

                        suffix = this.dark?"dark":"light"

                        // Select all images with the class 'themeable'
                        const images = document.querySelectorAll('.with-dark-light-theme');
                        
                        images.forEach(image => {
                            // Replace 'light' with 'dark' or vice versa in the image src path
                            if (suffix === 'dark' && image.src.includes('light')) {
                                image.src = image.src.replace('light', 'dark');
                            } else if (suffix === 'light' && image.src.includes('dark')) {
                                image.src = image.src.replace('dark', 'light');
                            }
                        });
                    }
                }
            }
        </script>
        """
    ).tag(sync=True)
    "Unicode: the javascript script to manually trigger the resize event"

    @observe("dark")
    def update_images(self, *_):
        """trigger the template method i.e. the resize event."""
        return self.send({"method": "updateImageSources"})
