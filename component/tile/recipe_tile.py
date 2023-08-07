from datetime import datetime

import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from traitlets import Int, Unicode, directional_link

import component.parameter as cp
from component.message import cm
from component.model import Recipe
from component.scripts import validation
from component.tile.custom_aoi_tile import AoiTile
from component.tile.dashboard_tile import DashboardTile
from component.tile.map_tile import MapTile

# Import types
from component.tile.questionnaire_tile import QuestionnaireTile
from component.widget.alert_state import AlertState

_content = {
    "new": ["mdi-newspaper-plus", cm.recipe.new.title, cm.recipe.new.desc],
    "load": ["mdi-upload", cm.recipe.load.title, cm.recipe.load.desc],
    "save": ["mdi-content-save", cm.recipe.save.title, cm.recipe.save.desc],
}


class CardAction(sw.Col):
    def __init__(self):
        super().__init__()
        self.xs12 = True
        self.sm4 = True

    def on_event(self, event, handler):
        self.btn.on_event(event, handler)


class CardNew(CardAction):
    def __init__(self):
        super().__init__()
        content = _content["new"]
        w_recipe_name = sw.TextField(
            label=cm.recipe.new.name,
            v_model=self.get_default_name(),
            hint=cm.recipe.new.hint,
            persistent_hint=True,
            class_="mt-5",
        )
        self.btn = v.Btn(
            children=[v.Icon(children=[content[0]]), content[1]], variant="text"
        )
        self.children = [
            sw.Card(
                hover=True,
                max_width=344,
                min_width=344,
                children=[
                    sw.CardTitle(children=[content[1]]),
                    sw.CardSubtitle(children=[content[2], w_recipe_name]),
                    sw.CardActions(children=[self.btn]),
                ],
            )
        ]

        w_recipe_name.on_event("blur", self._normalize_name)

    def get_default_name(self):
        """Define a default name for the recipe."""
        """name the recipe with the date."""
        now = datetime.now()
        return f'recipe_{now.strftime("%Y-%m-%d")}'

    def _normalize_name(self, widget, event, data):
        """Normalize the recipe name on blur as it will be used everywhere else."""
        not widget.v_model or setattr(
            widget, "v_model", su.normalize_str(widget.v_model)
        )


class CardLoad(CardAction):
    def __init__(self):
        super().__init__()
        content = _content["load"]
        self.btn = v.Btn(
            children=[v.Icon(children=[content[0]]), content[1]], variant="text"
        )
        self.children = [
            sw.Card(
                hover=True,
                max_width=344,
                min_width=344,
                children=[
                    sw.CardTitle(children=[content[1]]),
                    sw.CardSubtitle(children=[content[2]]),
                    sw.CardActions(children=[self.btn]),
                ],
            )
        ]


class CardSave(CardAction):
    def __init__(self):
        super().__init__()
        content = _content["save"]
        self.btn = v.Btn(
            children=[v.Icon(children=[content[0]]), content[1]], variant="text"
        )
        self.children = [
            sw.Card(
                hover=True,
                max_width=344,
                min_width=344,
                children=[
                    sw.CardTitle(children=[content[1]]),
                    sw.CardSubtitle(children=[content[2]]),
                    sw.CardActions(children=[self.btn]),
                ],
            )
        ]


class RecipeView(sw.Container):
    from_scratch = Int(0).tag(sync=True)
    """A trait to control once there is a new recipe loaded. It will be listed by RecipeTile and will build the different tiles."""

    recipe_path = Unicode(None, allow_none=True).tag(sync=True)
    """Validated path to the recipe file, it will come from the load dialog."""

    def __init__(self):
        self.attributes = {"_metadata": "recipe_tile"}

        super().__init__()
        self.recipe = None
        self.alert = AlertState().show()

        card_new = CardNew()
        card_load = CardLoad()
        card_save = CardSave()

        self.load_dialog = LoadDialog(self.recipe)

        self.children = [
            sw.Row(
                justify="center",
                children=[
                    sw.Col(
                        cols=12,
                        children=[sw.Html(tag="h1", children=["Welcome to SE.Plan"])],
                    )
                ],
            ),
            sw.Row(justify="center", children=[card_new, card_load, card_save]),
            self.alert,
            self.load_dialog,
        ]

        directional_link((self.load_dialog, "recipe_path"), (self, "recipe_path"))

        card_new.on_event("click", self.new_event)
        card_load.on_event("click", lambda *args: self.load_dialog.show())
        card_save.on_event("click", self.save_event)

        self.load_dialog.btn_load.on_event("click", self.load_event)

    def update_messages(self, change):
        """Update custom alert messages based on the UI build state.

        This method is called every time the build_state of the recipe changes,
        and it changes everytime the build state ("building", "done", "error")
        of one of the components changes.

        """
        for component_id, state in change["new"].items():
            self.alert.update_state(component_id, state)

    def new_event(self, *_):
        """Creates a new recipe from scratch."""
        # consider first when theres is not a recipe loaded
        if self.from_scratch == 0:
            self.recipe = Recipe()
            self.recipe.load_model()
            self.recipe.observe(self.update_messages, "build_state")
            self.from_scratch += 1

        # if there is a recipe already loaded, we have to ask the user if he wants to save it
        # and then reset the recipe to start from scratch.

        self.recipe.reset()

        # Let the user know that there might be some unsaved changes
        # let the user select a name
        # reset or create new values?
        # I have to reset, because the other components were already created with
        # the default recipe
        # We have to make this name fully available to the other components...
        # Perhaps we can display the name always in the menu bar?

        # only set the questionnaires if there's not already a recipe.
        # it is less expensive to reset the recipe than to create a new one.

    def load_event(self, *args):
        """Load the recipe and close the dialog."""
        if not self.load_dialog.recipe_path:
            return

        if not self.recipe:
            self.recipe = Recipe()
            self.recipe.load_model()
            self.recipe.observe(self.update_messages, "build_state")

        self.recipe.load(self.load_dialog.recipe_path)

    def save_event(self, *_):
        """Saves the current state of the recipe."""

        # just save the current recipe (get all the values from Recipe) and use the
        # same name of the session.
        # If the recipe already exists, ask the user if he wants to overwrite it, or not?

        # I can also create a switch button to overwrite the current file.


class LoadDialog(v.Dialog):
    """Dialog to load a recipe from a file."""

    recipe_path = Unicode(None, allow_none=True).tag(sync=True)

    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.recipe_path = None

        super().__init__()

        # set some default parameters
        self.max_width = 500
        self.v_model = False
        self.persistent = True

        # Create input file widget wrapped in a layout
        self.w_input_recipe = sw.FileInput(
            ".json", folder=cp.result_dir, root=cp.result_dir
        )

        self.btn_load = sw.Btn(cm.recipe.load.dialog.load)
        self.btn_cancel = sw.Btn(
            cm.recipe.load.dialog.cancel, outlined=True, class_="ml-2"
        )

        # assemlble the layout
        self.children = [
            v.Card(
                class_="pa-4",
                children=[
                    sw.CardTitle(children=[cm.recipe.load.dialog.title]),
                    sw.CardText(children=[self.w_input_recipe]),
                    self.btn_load,
                    self.btn_cancel,
                ],
            )
        ]

        # Create events
        self.btn_cancel.on_event("click", self.cancel)
        self.w_input_recipe.observe(self.validate_input, "v_model")

    @su.switch("loading", on_widgets=["btn_load"])
    def validate_input(self, change):
        """Validate the recipe file."""
        # Get TextField from w_file_name widget
        text_field_msg = change["owner"].children[-1]

        # Reset any previous error messages
        text_field_msg.error_messages = []

        # Validate the recipe file and show errors if there are
        self.recipe_path = validation.validate_recipe(change["new"], text_field_msg)

    def show(self):
        """Display the dialog and write down the text in the alert."""
        self.valid = False
        self.v_model = True

    def cancel(self, *args):
        """Hide the widget and reset the selected file."""
        self.w_input_recipe.reset()
        self.recipe_path = None
        self.v_model = False

        return


class RecipeTile(sw.Layout):
    def __init__(
        self,
        recipe_view: RecipeView,
        aoi_tile: AoiTile,
        questionnaire_tile: QuestionnaireTile,
        map_tile: MapTile,
        dashboard_tile: DashboardTile,
    ):
        super().__init__()

        self.aoi_tile = aoi_tile
        self.questionnaire_tile = questionnaire_tile
        self.map_tile = map_tile
        self.dashboard_tile = dashboard_tile
        self.recipe_view = recipe_view

        self.children = [self.recipe_view]

        self.recipe_view.observe(self.render, "from_scratch")

    def render(self, *args):
        """Render all the different tiles.

        This element is intended to be used only once, when the app has to start.
        """
        self.aoi_tile.build(self.recipe_view.recipe)
        self.questionnaire_tile.build(self.recipe_view.recipe)
        self.map_tile.build(self.recipe_view.recipe)
        self.dashboard_tile.build(self.recipe_view.recipe)
