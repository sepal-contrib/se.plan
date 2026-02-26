from datetime import datetime
from pathlib import Path
from typing import Literal

import ipyvuetify as v
from component.frontend.icons import icon
from component.widget.buttons import TextBtn
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from sepal_ui.scripts.decorator import loading_button, switch
from traitlets import Int, Unicode, directional_link, observe

from component.message import cm
from component.model.app_model import AppModel
from component.model.recipe import Recipe
from component.scripts.validation import ValidationResult, sanitize_recipe_data

# Import types
from component.widget.alert_state import Alert, AlertDialog, AlertState
from component.widget.base_dialog import BaseDialog
from component.widget.custom_widgets import RecipeInput
from component.widget.invalid_data_dialog import InvalidDataDialog
import logging

logger = logging.getLogger("SEPLAN")

_content = {
    "new": {
        "icon": icon("recipe-note"),
        "btn": cm.recipe.new.btn,
        "desc": cm.recipe.new.desc,
        "title": cm.recipe.new.title,
    },
    "load": {
        "icon": icon("upload"),
        "btn": cm.recipe.load.btn,
        "desc": cm.recipe.load.desc,
        "title": cm.recipe.load.title,
    },
    "save": {
        "icon": icon("save"),
        "btn": cm.recipe.save.btn,
        "desc": cm.recipe.save.desc,
        "title": cm.recipe.save.title,
    },
}


class CardAction(sw.Card):
    """Base class for the cards with an action button."""

    def __init__(self, content):
        super().__init__()
        self.hover = True
        self.min_width = 344
        self.btn = TextBtn(content["btn"], gliph=content["icon"])
        self.children = [
            sw.CardActions(children=[sw.Spacer(), self.btn]),
        ]


class CardLoad(CardAction):
    """Card to load a recipe. It will open a dialog to select a recipe file."""

    def __init__(self):
        content = _content["load"]
        super().__init__(content)
        children = [
            sw.CardTitle(children=[content["title"]]),
            sw.CardSubtitle(children=[content["desc"]]),
        ]
        self.set_children(children, "first")


class CardNewSave(CardAction):
    """Card to create a new recipe or save the current one."""

    recipe_name = Unicode("", allow_none=True).tag(sync=True)
    "str: given name of the recipe, captured by w_recipe_name"

    def __init__(self, type_: Literal["new", "save"]):
        content = _content[type_]
        super().__init__(content)
        self.w_recipe_name = sw.TextField(
            label=cm.recipe.new.text_field_label,
            v_model="",
            hint=cm.recipe.new.hint,
            persistent_hint=True,
            class_="mt-5",
            suffix=".json",
        )

        children = [
            sw.CardTitle(children=[content["title"]]),
            sw.CardSubtitle(children=[content["desc"], self.w_recipe_name]),
        ]

        self.set_children(children, "first")

        self.w_recipe_name.on_event("blur", self._normalize_name)
        self.observe(self._on_change, "recipe_name")

        if type_ == "new":
            self.recipe_name = self.get_default_name()

    def get_default_name(self):
        """Define a default name for the recipe name the recipe with the date."""
        now = datetime.now()
        return f'recipe_{now.strftime("%Y-%m-%d-%H%M%S")}'

    def _normalize_name(self, widget, event, data):
        """Normalize the recipe name on blur as it will be used everywhere else."""
        if widget.v_model:
            name = su.normalize_str(widget.v_model)
            widget.v_model = name
            self.recipe_name = name

    def _on_change(self, change):
        """Update the recipe name in the recipe object."""
        if change["new"]:
            self.w_recipe_name.v_model = change["new"]


class RecipeView(sw.Layout):
    create_view = Int(0).tag(sync=True)
    """A trait to control once there is a new recipe loaded. It will be listed by RecipeTile and will build the different tiles."""

    load_recipe_path = Unicode(None, allow_none=True).tag(sync=True)
    """Path of a validated recipe file, it will come from the load dialog."""

    recipe_session_path = Unicode(None, allow_none=True).tag(sync=True)
    """Normalized recipe path of the current session. It will come from NewCard/LoadCard"""

    # app_model: AppModel
    # """It will be used to listen the on_save trait and trigger the save button here"""

    def __init__(
        self, recipe: Recipe = None, app_model: AppModel = None, sepal_session=None
    ):
        self.attributes = {"_metadata": "recipe_tile"}
        self._metadata = {"mount_id": "recipe_tile"}

        super().__init__()
        self.recipe = recipe
        self.alert = AlertState()
        self.alert_dialog = AlertDialog(self.alert)

        # Store pending validation result for dialog callbacks
        self._pending_validation = None

        self.app_model = app_model
        if not app_model:
            self.app_model = AppModel()

        self.card_new = CardNewSave(type_="new")
        self.card_load = CardLoad()
        self.card_save = CardNewSave(type_="save")

        self.load_dialog = LoadDialog(sepal_session=sepal_session)

        # Create the invalid data dialog with callbacks
        self.invalid_data_dialog = InvalidDataDialog(
            on_continue_callback=self._continue_with_cleaned_data,
            on_cancel_callback=self._cancel_recipe_load,
        )

        self.children = [
            self.alert_dialog,
            self.load_dialog,
            self.invalid_data_dialog,
            sw.Container(
                children=[
                    sw.Row(
                        justifyContent="center",
                        children=[
                            sw.Col(cols="12", sm12=True, children=[self.card_new]),
                            sw.Col(cols="12", sm12=True, children=[self.card_load]),
                            sw.Col(cols="12", sm12=True, children=[self.card_save]),
                        ],
                    ),
                ]
            ),
        ]

        directional_link(
            (self, "recipe_session_path"), (self.recipe, "recipe_session_path")
        )

        # link the current session path with save_card.recipe_name
        self.observe(self.session_path_handler, "recipe_session_path")

        # Capture errors with alert (we have to decorate before the events definition)
        self.new_event = loading_button(alert=self.alert, button=self.card_new.btn)(
            self.new_event
        )
        self.load_event = loading_button(alert=self.alert, button=self.card_load.btn)(
            self.load_event
        )
        self.save_event = loading_button(alert=self.alert, button=self.card_save.btn)(
            self.save_event
        )

        # Create events
        self.card_new.btn.on_event("click", self.new_event)
        self.card_load.btn.on_event("click", lambda *_: self.load_dialog._show())

        self.load_dialog.btn_load.on_event("click", self.load_event)

        self.card_save.btn.on_event("click", self.save_event)
        self.app_model.observe(self.save_event, "on_save")

        directional_link((self, "recipe_session_path"), (self.app_model, "recipe_name"))

        # link the recipe new_changes counter to the app new_changes counter
        directional_link((self.recipe, "new_changes"), (self.app_model, "new_changes"))

    @observe("recipe_session_path")
    def test_recipe_path(self, change):
        """Test if the recipe path is valid."""
        print("testoutput")
        logger.debug(f"Testing recipe path: {self.recipe_session_path}")

    def session_path_handler(self, change):
        """handle current session path and link its value with save_card.recipe_name."""
        # we only need to show the name, not the full path, but we have to keep the full path
        # to save the recipe

        self.card_save.recipe_name = str(Path(change["new"]).stem)

    @switch("disabled", on_widgets=["card_new", "card_load", "card_save"])
    @switch("loading", on_widgets=["card_new"])
    def new_event(self, *_):
        """Creates a new recipe from scratch."""
        self.alert.reset()

        if not self.card_new.recipe_name:
            raise ValueError(cm.recipe.error.no_name)

        self.alert.set_state("reset", "all", "building")
        self.recipe.reset()
        self.alert.set_state("reset", "all", "done")

        # update current session path
        self.recipe_session_path = self.recipe.get_recipe_path(
            self.card_new.recipe_name
        )

    @switch("disabled", on_widgets=["card_new", "card_load", "card_save"])
    @switch("loading", on_widgets=["card_load"])
    def load_event(self, *_):
        """Load the recipe and close the dialog.

        This event is linked with dialog.load button from dialog.
        """
        self.alert.reset()

        # If there is not recipe path, it means there is not a valid recipe file.
        # we wonnt' let them close the dialog until they select a valid recipe file.
        # or cancel the dialog.
        if not self.load_dialog.load_recipe_path:
            return

        self.load_recipe_path = self.load_dialog.load_recipe_path

        self.load_dialog.close_dialog()

        self.alert.set_state("load", "all", "building")

        logger.debug(f"Recipe session {self.recipe.sepal_session}")

        # Load recipe - returns ValidationResult if errors found
        result = self.recipe.load(recipe_path=self.load_dialog.load_recipe_path)

        # Check if validation failed
        if isinstance(result, ValidationResult):
            logger.warning(
                f"Recipe validation failed with {result.total_errors} errors"
            )

            # Store for callbacks to use
            self._pending_validation = result

            # Clear the building state
            self.alert.set_state("load", "all", "done")

            # Show dialog with all error types
            self.invalid_data_dialog.show_errors(
                benefits_errors=result.benefits_errors,
                constraints_errors=result.constraints_errors,
                costs_errors=result.costs_errors,
            )

            # Don't set recipe_session_path yet - wait for user decision
            return

        # Success - recipe loaded normally
        self._pending_validation = None

        # Assign the recipe path to the current session path
        self.recipe_session_path = self.load_dialog.load_recipe_path

        self.alert.set_state("load", "all", "done")

    def save_event(self, *_):
        """Saves the current state of the recipe."""
        self.alert.reset()

        # consider first when theres is not a recipe loaded
        if not self.recipe.seplan_aoi:
            raise Exception(cm.recipe.error.no_seplan)
            return

        if not self.card_save.recipe_name:
            raise ValueError(cm.recipe.error.no_name)

        # If there's not recipe path (there's not an active recipe), we'll create a new path
        if not self.recipe_session_path:
            recipe_path = self.recipe.get_recipe_path(self.card_save.recipe_name)

        # If there's already a recipe_session_path and/or not recipe name changed.
        # just save the recipe in the same folder but with the same/different name
        else:
            recipe_path = (
                Path(self.recipe_session_path)
                .with_name(self.card_save.recipe_name)
                .with_suffix(".json")
            )

        self.recipe.save(recipe_path)

        # Assign the recipe path to the current session path
        self.recipe_session_path = str(recipe_path)

        self.alert.add_msg(cm.recipe.states.save.format(recipe_path), type_="success")

    def _continue_with_cleaned_data(self):
        """
        Continue working with the cleaned data after user accepts.

        This is called when the user clicks "Continue" in the invalid data dialog.
        The data will be sanitized and loaded into the models.
        """
        if not self._pending_validation:
            logger.error("No pending validation to continue")
            return

        try:
            logger.info("User chose to continue - sanitizing and loading data")

            # Sanitize the data (clears invalid values)
            sanitized_data = sanitize_recipe_data(
                self._pending_validation.raw_data, self._pending_validation
            )

            # Load the sanitized data
            self.recipe.load_sanitized(
                sanitized_data, self._pending_validation.recipe_path
            )

            # Assign the recipe path to the current session path
            self.recipe_session_path = self._pending_validation.recipe_path

            # Show success message with error count
            error_count = self._pending_validation.total_errors
            self.alert.add_msg(
                f"Recipe loaded with {error_count} invalid item(s) sanitized (values cleared)",
                type_="warning",
            )

            # Clear pending validation
            self._pending_validation = None

        except Exception as e:
            logger.exception(f"Error loading sanitized recipe: {e}")
            self.alert.add_msg(f"Error loading recipe: {str(e)}", type_="error")
            # Keep pending validation in case user wants to retry
            raise

    def _cancel_recipe_load(self):
        """
        Cancel the recipe load and reset to default values.

        This is called when the user clicks "Cancel" in the invalid data dialog.
        """
        if not self._pending_validation:
            logger.error("No pending validation to cancel")
            return

        logger.info("User cancelled recipe load - resetting to defaults")

        # Always clear pending validation first
        self._pending_validation = None

        try:
            # Reset all models to default state
            self.recipe.reset()

            # Clear recipe path
            self.recipe_session_path = ""

            # Update the alert
            self.alert.add_msg(
                "Recipe load cancelled - reset to defaults", type_="info"
            )

        except Exception as e:
            logger.exception(f"Error resetting recipe: {e}")
            self.alert.add_msg(f"Error resetting recipe: {str(e)}", type_="error")
            # Don't re-raise - dialog is already closed


class LoadDialog(BaseDialog):
    """Dialog to load a recipe from a file."""

    load_recipe_path = Unicode(None, allow_none=True).tag(sync=True)

    def __init__(self, alert: Alert = None, sepal_session=None):

        self.alert = alert or Alert()
        self.load_recipe_path = None

        super().__init__()

        # Create input file widget wrapped in a layout
        self.w_input_recipe = RecipeInput(sepal_session=sepal_session)

        self.btn_load = TextBtn(cm.recipe.load.dialog.load)
        self.btn_cancel = TextBtn(cm.recipe.load.dialog.cancel, outlined=True)

        # assemlble the layout
        self.children = [
            v.Card(
                class_="pa-4",
                children=[
                    sw.CardTitle(children=[cm.recipe.load.dialog.title]),
                    sw.CardText(children=[self.w_input_recipe]),
                    sw.CardActions(
                        children=[
                            sw.Spacer(),
                            self.btn_load,
                            self.btn_cancel,
                        ]
                    ),
                ],
            )
        ]

        # Create events
        self.btn_cancel.on_event("click", self.cancel)
        directional_link(
            (self.w_input_recipe, "load_recipe_path"), (self, "load_recipe_path")
        )

    def open_dialog(self, *args, **kwargs):
        """Prepare and open the dialog without calling super().show()."""
        # Reset selection and validation state before opening
        self.load_recipe_path = None
        self.w_input_recipe.file_input.error_messages = []
        self.w_input_recipe.file_input.reset()
        self.valid = False
        # Open via BaseDialog's open_dialog (not super().show())
        super().open_dialog()

    def _show(self, *args, **kwargs):
        """Override show to route to open_dialog with custom prep."""
        return self.open_dialog(*args, **kwargs)

    def cancel(self, *args):
        """Hide the widget and reset the selected file."""
        self.w_input_recipe.reset()
        self.load_recipe_path = None
        self.close_dialog()

        return
