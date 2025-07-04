from pathlib import Path
from typing import Literal, Union

from component.frontend.icons import icon
from component.model.recipe import Recipe
from component.scripts import validation
from component.widget.base_dialog import BaseDialog
from component.widget.expression import ExpressionBtn
import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from sepal_ui.scripts.sepal_client import SepalClient
from sepal_ui.sepalwidgets.btn import TaskButton

from component import widget as cw


from sepal_ui.frontend.styles import get_theme
from traitlets import Bool, Dict, Int, Unicode, directional_link, link, observe
from sepal_ui.sepalwidgets.widget import Markdown
import ipyvuetify as v
import component.parameter as cp


from component.message import cm
from component.model import BenefitModel, ConstraintModel, CostModel, SeplanAoi
from component.scripts.seplan import Seplan
from component.widget.alert_state import Alert, AlertDialog
from component.widget.preview_theme_btn import PreviewThemeBtn
from component.widget.buttons import IconBtn, TextBtn

from .benefit_dialog import BenefitDialog
from .constraint_dialog import ConstraintDialog
from .cost_dialog import CostDialog

from sepal_ui.sepalwidgets.file_input import FileInput as FileInputElement
import logging

logger = logging.getLogger("SEPLAN")


class ResizeTrigger(v.VuetifyTemplate):
    """Update the image source when the theme changes."""

    dark = Bool(v.theme.dark, allow_none=True).tag(sync=True)
    template = Unicode(
        """
        <script class='sepal-ui-script'>
            {
                methods: {
                    jupyter_resize() {
                        /* force the resize event. useful for drawer clicks*/
                        window.dispatchEvent(new Event("resize"));
                    }
                }
            }
        </script>
        """
    ).tag(sync=True)
    "Unicode: the javascript script to manually trigger the resize event"

    def resize(self):
        """trigger the template method i.e. the resize event."""
        return self.send({"method": "resize"})


class RecipeInspector(v.VuetifyTemplate):

    template_file = Unicode(str(Path(__file__).parent / "vue/recipe_reader.vue")).tag(
        sync=True
    )
    data_dict = Dict().tag(sync=True)
    dialog = Bool(False).tag(sync=True)
    recipe_name = Unicode("").tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_data(self, data: dict, recipe_name: str):
        self.open_dialog()
        self.recipe_name = recipe_name
        self.data_dict = data

    def open_dialog(self, *_):

        self.dialog = True

    def close_dialog(self, *_):

        self.dialog = False

    def reset(self):
        self.data_dict = {}
        self.recipe_name = ""


class RecipeInput(sw.Layout):

    load_recipe_path = Unicode(None, allow_none=True).tag(sync=True)
    valid = Bool(False).tag(sync=True)
    v_model = Unicode(None, allow_none=True).tag(sync=True)

    def __init__(
        self,
        main_recipe: Recipe = None,
        sepal_session: SepalClient = None,
        attributes={},
    ):
        super().__init__(attributes=attributes)
        self.sepal_session = sepal_session
        self.recipe_inspector = RecipeInspector()
        self.file_input = FileInputElement(
            sepal_client=self.sepal_session,
            extensions=[".json"],
            initial_folder="module_results/se.plan",
        )
        self.file_input.observe(self.validate_input, "v_model")

        self.btn_view = TextBtn(cm.recipe.load.dialog.view, class_="ml-2")
        self.btn_view.on_event("click", self.view_event)
        self.children = [
            sw.Row(
                children=[self.file_input, self.btn_view, self.recipe_inspector],
                class_="flex align-center",
            )
        ]

        directional_link((self.file_input, "v_model"), (self, "v_model"))

    def validate_input(self, change):
        """Validate the recipe file."""

        if not change["new"]:
            logger.debug("validating recipe: no file selected")
            self.load_recipe_path = None
            self.valid = False
            return

        # Reset any previous error messages
        self.valid = False
        self.file_input.error_messages = []
        self.load_recipe_path = None

        # Validate the recipe file and show errors if there are
        self.load_recipe_path = validation.validate_recipe(
            change["new"], self.file_input, self.sepal_session
        )
        self.valid = bool(self.load_recipe_path)

    def view_event(self, *_):
        """View the recipe in a dialog."""

        if not self.load_recipe_path:
            return

        recipe_path, data = validation.read_recipe_data(
            self.load_recipe_path, self.sepal_session
        )
        self.recipe_inspector.set_data(data, recipe_name=str(Path(recipe_path)))


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

        self.w_new = TextBtn(f"New {name}", gliph=icon("plus"), type_="success")

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
    def __init__(
        self, model: Seplan, alert: Alert = None, gee_interface=None, sepal_session=None
    ) -> None:
        super().__init__()

        alert = alert or Alert()

        self.sepal_session = sepal_session
        self.gee_interface = gee_interface
        self.height = "48px"
        self.model = model
        self.elevation = 0
        self.color = "accent"

        self.btn_download = TaskButton(
            cm.dashboard.toolbar.btn.download.title, small=True
        )
        self.btn_dashboard = TaskButton(
            cm.dashboard.toolbar.btn.compute.title, small=True
        )

        self.btn_compare = IconBtn(gliph=icon("compare")).set_tooltip(
            cm.dashboard.toolbar.btn.compare.tooltip, right=True, max_width="200px"
        )

        self.compare_dialog = cw.CompareScenariosDialog(
            type_="chart",
            alert=alert,
            sepal_session=sepal_session,
            gee_interface=self.gee_interface,
        )

        self.btn_compare.on_event("click", lambda *_: self.compare_dialog.open_dialog())

        self.children = [
            self.btn_download.children,
            sw.Spacer(),
            self.btn_compare.with_tooltip,
            sw.Divider(vertical=True, class_="mr-2"),
            self.btn_dashboard.children,
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

        self.resize_trigger = ResizeTrigger()

        self.children = [self.resize_trigger] + self.children

        self.observe(self.add_notif, "alert")

    def callback(self, *args) -> None:
        """Callback to be executed when the item is clicked."""

        self.resize_trigger.resize()

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

        # Close all dialogs when a drawer item is clicked
        self.app_model.close_all_dialogs += 1

        return self


class CustomAppBar(sw.AppBar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.save_recipe_btn = IconBtn(gliph=icon("save"))
        self.save_recipe_btn.color = "#f3f3f3"
        self.save_recipe_btn.v_icon.left = False

        self.recipe_holder = sw.Flex(
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
                self.save_recipe_btn,
            ],
        )

        self.children = self.children[:3] + [self.recipe_holder] + self.children[3:]
        self.recipe_holder.hide()

    def update_recipe(
        self, element: Literal["recipe_name", "new_changes"], value: str = ""
    ) -> None:
        """Update the recipe name and state in the app bar."""

        self.recipe_holder.show()

        if not value:
            return

        if element == "new_changes":
            value = cm.app.recipe_state[value]

        self.get_children(attr="id", value=element)[0].children = value


class CustomApp(sw.App):
    def __init__(self, app_model, theme_toggle=None, *args, **kwargs):
        super().__init__(*args, theme_toggle=theme_toggle, **kwargs)

        self.app_model = app_model
        self.app_model.observe(self.update_recipe_state, "recipe_name")
        self.app_model.observe(self.update_recipe_state, "new_changes")
        self.app_model.observe(self.close_all_dialogs, "close_all_dialogs")

        self.appBar.save_recipe_btn.on_event("click", self.save_recipe)

        self.show_tile("about_tile")

    def save_recipe(self, *_):
        """Save the recipe in the app model."""
        self.app_model.on_save += 1

    def update_recipe_state(self, change):
        """Update the recipe state in the app bar."""

        # logger.debug(f"Updating recipe state: {change}")

        if not change["new"]:
            change["new"] = ""

        if change["name"] == "new_changes":
            change["new"] = "unsaved" if change["new"] else "saved"
        else:
            change["new"] = change["new"].split("/")[-1].replace(".json", "")

        self.appBar.update_recipe(element=change["name"], value=change["new"])

    def close_all_dialogs(self, *args):
        """Close all dialogs in the app."""

        dialogs = self.get_children(klass=BaseDialog)
        alert_dialogs = self.get_children(klass=AlertDialog)
        for dialog in dialogs + alert_dialogs:
            dialog.close_dialog()


class CustomTileAbout(sw.Tile):
    def __init__(self, pathname: Union[str, Path], theme_toggle=None, **kwargs) -> None:
        """Create an about tile using a .md file.

        This tile will have the "about_widget" id and "About" title.

        Args:
            pathname: the path to the .md file
        """

        text = Path(pathname).read_text()

        # Search any url in the text and look for the dark/light theme
        text = (
            text.replace("/light/", "/dark/")
            if theme_toggle.dark
            else text.replace("/dark/", "/light/")
        )

        content = Markdown(text)

        update_script = UpdateImages(theme_toggle)
        super().__init__("about_tile", "About", inputs=[content, update_script])

        directional_link((theme_toggle, "dark"), (update_script, "dark"))


class UpdateImages(v.VuetifyTemplate):
    """Update the image source when the theme changes."""

    dark = Bool(None, allow_none=True).tag(sync=True)
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

    def __init__(self, theme_toggle, **kwargs):
        super().__init__(**kwargs)
        self.dark = theme_toggle.dark
        self.observe(self.update_images, "dark")

    def update_images(self, *_):
        """trigger the template method i.e. the resize event."""
        return self.send({"method": "updateImageSources"})
