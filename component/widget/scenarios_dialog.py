"""UI component widget to compare different scenarios."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from typing import List, Literal
from component.model.recipe import Recipe
from component.scripts import gee
from component.scripts.statistics import get_summary_statistics
from component.scripts.validation import are_comparable, validate_scenarios_recipes
from component.types import RecipeInfo, RecipePaths
from component.widget.alert_state import Alert
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import IconBtn
import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from component.widget.custom_widgets import RecipeInput, TableIcon, TextBtn
from ipyleaflet import SplitMapControl
from traitlets import Dict as Dict, Int
from sepal_ui.mapping import SepalMap
import component.scripts.gee as gee
from component import parameter as cp
from sepal_ui.scripts.decorator import loading_button

from component.widget.map import SeplanMap


class CompareScenariosDialog(BaseDialog):
    """Dialog to compare multiple scenarios from recipes."""

    def __init__(
        self,
        type_: Literal["map", "chart"],
        map_: SepalMap = None,
        alert: Alert = None,
        main_recipe: Recipe = None,
        trashable: bool = False,
        increaseable: bool = False,
        limit: int = 2,
        overall_dashboard=None,
        theme_dashboard=None,
    ):
        super().__init__()

        self.map_ = map_
        self.alert = alert or Alert()
        self.overall_dashboard = overall_dashboard
        self.theme_dashboard = theme_dashboard

        if type_ == "chart":
            trashable = True
            increaseable = True
            limit = 5

        else:
            if not map_:
                raise ValueError("A map must be provided to compare maps.")

        # Create UI elements for up to 2 scenario inputs
        self.scenario_inputs = ScenarioInputs(
            main_recipe=main_recipe if main_recipe else None,
            limit=limit,
            trashable=trashable,
            increaseable=increaseable,
        )
        self.btn_compare_map = TextBtn("Compare maps")
        self.btn_compare_stat = TextBtn("Compare statistics")

        self.btn_cancel = TextBtn("Cancel", outlined=True)

        # Assemble the layout
        scenario_inputs_layout = v.Layout(
            children=[self.scenario_inputs], class_="pa-0 ma-0"
        )

        self.actions = sw.CardActions(children=[])
        self.children = [
            v.Card(
                attributes={"id": "card_content"},
                class_="ma-0 ",
                children=[
                    sw.CardTitle(children=["Compare Scenarios"]),
                    sw.CardText(children=[scenario_inputs_layout]),
                    self.alert,
                    self.actions,
                ],
            )
        ]

        self.set_actions(type_)

        self.compare_layers = loading_button(self.alert, self.btn_compare_map)(
            self.compare_layers
        )

        self.compare_statistics = loading_button(self.alert, self.btn_compare_stat)(
            self.compare_statistics
        )

        self.btn_compare_map.on_event("click", self.compare_layers)
        self.btn_compare_stat.on_event("click", self.compare_statistics)
        self.btn_cancel.on_event("click", self.close_dialog)

    def set_actions(self, type_: Literal["map", "chart"]):
        """Set the actions for the dialog based on the type of comparison."""

        btn = self.btn_compare_map if type_ == "map" else self.btn_compare_stat
        self.actions.children = [sw.Spacer(), btn, self.btn_cancel]

    def validate_scenarios(self):
        """Validate that all selected scenarios have the same AOI."""

        # First validate that all of them are valid
        validate_scenarios_recipes(self.scenario_inputs.recipe_paths)
        are_comparable(self.scenario_inputs.recipe_paths)

    def read_recipes(self) -> List[Recipe]:
        """Load the recipes from the recipe paths."""

        recipes = []
        self.validate_scenarios()

        for _, recipe_data in self.scenario_inputs.recipe_paths.items():
            recipe_path = recipe_data["path"]
            recipe = Recipe()
            recipe.load(recipe_path)
            recipes.append(recipe)

        return recipes

    def compare_layers(self, widget, event, data, map_: SeplanMap = None):
        """Add suitability indices as layers to the map."""

        map_ = map_ or self.map_

        # Remove all layers from the map
        map_.remove_all()

        # Remove previous layer controls
        map_.controls = [
            control
            for control in map_.controls
            if not isinstance(control, SplitMapControl)
        ]

        # Read the recipes
        recipes = self.read_recipes()

        # Assert that there must be only two recipes
        assert len(recipes) == 2, "Only two recipes can be compared."

        def process_recipe(recipe, gee, cp):
            layer_name = recipe.get_recipe_name()
            return gee.get_layer(
                recipe.seplan.get_constraint_index()
                .unmask(0)
                .clip(recipe.seplan_aoi.feature_collection),
                cp.layer_vis,
                layer_name,
            )

        # Create a ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            # Submit tasks to the executor
            futures = [
                executor.submit(process_recipe, recipe, gee, cp) for recipe in recipes
            ]

            # Collect the results
            layers = [future.result() for future in futures]

        map_.centerObject(recipes[0].seplan_aoi.feature_collection)
        layer_control = SplitMapControl(left_layer=layers[0], right_layer=layers[1])
        map_.add(layer_control)
        self.close_dialog()

    def set_stats_content(self, overall_dashboard=None, theme_dashboard=None):
        """Set the content of the statistics dashboard."""

        self.overall_dashboard = overall_dashboard
        self.theme_dashboard = theme_dashboard

    def compare_statistics(self, *args):
        """Compute and display summary statistics."""

        if not self.overall_dashboard or not self.theme_dashboard:

            self.overall_dashboard = sw.Card()
            self.theme_dashboard = sw.Card()

            self.children = self.children + [
                self.overall_dashboard,
                self.theme_dashboard,
            ]

        recipes = self.read_recipes()

        recipe_summary_stats = [get_summary_statistics(recipe) for recipe in recipes]

        self.overall_dashboard.set_summary(recipes_stats=recipe_summary_stats)
        self.theme_dashboard.set_summary(recipes, recipes_stats=recipe_summary_stats)

        # Close the dialog
        self.close_dialog()


class ScenarioInputs(sw.Layout):
    """Returns a widget that can add dinamically fileInputs."""

    recipe_paths: RecipePaths = Dict({}).tag(sync=True)
    """Dicionary of recipe paths."""

    idx = Int(0).tag(sync=True)

    limited_reached = Int(0).tag(sync=True)
    "will be increased when user tries to add more inputs than the limit."

    def __init__(
        self,
        main_recipe: Recipe = None,
        limit=2,
        trashable=False,
        increaseable=False,
    ):

        self.class_ = "d-block"
        self.recipe_limit = limit

        super().__init__()

        # Add btn
        btn_add = IconBtn("mdi-plus", color="primary", class_="mr-2")
        btn_add.on_event("click", self.add_input)
        main_recipe = self.get_input_row(trashable=trashable, main_recipe=main_recipe)

        action_header = sw.Html(
            tag="th",
            children=[v.Layout(children=["Action"])],
            style_="text-align: center;",
        )
        file_input_header = sw.Html(
            tag="th",
            style_="text-align: center;",
            children=[
                v.Layout(
                    children=["Recipe", v.Spacer(), btn_add if increaseable else ""]
                )
            ],
        )

        headers = sw.Html(
            tag="tr",
            children=(
                [action_header, file_input_header] if trashable else [file_input_header]
            ),
        )

        self.tbody = sw.Html(
            attributes={"id": "tbody"},
            tag="tbody",
            children=[main_recipe, self.get_input_row(trashable=trashable)],
        )
        self.table = sw.SimpleTable(
            dense=False,
            children=[
                sw.Html(tag="thead", children=[headers]),
                self.tbody,
            ],
        )

        self.children = [self.table]

    def get_limit(self) -> int:
        """Count the number of inputs in the widget and return the number of inputs left."""

        return self.recipe_limit - len(self.recipe_paths)

    def add_input(self, *args):
        """Add a new input row to the widget."""

        if self.get_limit() > 0:
            self.tbody.children = self.tbody.children + [self.get_input_row()]

        else:
            self.limited_reached += 1

    def get_id_name(self, idx: int) -> str:
        """Get the name of the input based on the index."""

        return "recipe_path_" + str(idx)

    def remove_input_row(self, input_id: int):
        """Remove and dispose the a given file input."""

        row_to_remove = self.get_children(attr="id", value=input_id)

        if row_to_remove:
            # Unobserve the input
            remove_btn, file_input = row_to_remove[0].children
            file_input.unobserve(self.update_recipe_paths, "v_model")
            remove_btn.unobserve(self.remove_input_row, "click")

            # Remove the recipe path, I need to reassign the dictionary
            self.recipe_paths = {
                key: value
                for key, value in self.recipe_paths.items()
                if key != input_id
            }

            # Remove the row from the children
            self.tbody.children = [
                child for child in self.tbody.children if child != row_to_remove[0]
            ]

    def get_input_row(self, trashable=True, main_recipe: Recipe = None) -> v.Html:
        """Get a new file input."""

        row_id = self.get_id_name(self.idx)

        if trashable:

            remove_btn = TableIcon(
                "mdi-trash-can", name="trash", small=False, disabled=True
            )
            remove_btn_td = sw.Html(
                style_="width: 65px", tag="td", children=[remove_btn]
            )

            # Only allow to remove the row if there are more than three rows
            if len(self.recipe_paths) >= 2:
                remove_btn.disabled = False
                remove_btn.on_event(
                    "click", lambda *args: self.remove_input_row(row_id)
                )

        file_input = RecipeInput(attributes={"id": row_id}, default_recipe=main_recipe)
        file_input.observe(self.update_recipe_paths, ["v_model", "valid"])
        file_input_td = sw.Html(tag="td", children=[file_input])

        # Set the structure of the recipe_paths
        row_info: RecipeInfo = {"path": file_input.v_model, "valid": False}
        self.recipe_paths.setdefault(row_id, row_info)
        self.idx += 1

        return sw.Html(
            tag="tr",
            style_="width: 65px; text-align: center; vertical-align: middle;",
            attributes={"id": row_id},
            children=[remove_btn_td, file_input_td] if trashable else [file_input_td],
        )

    def update_recipe_paths(self, change: dict):
        """Update the list of recipe paths."""

        recipe_id: str = change["owner"].attributes["id"]
        value_name = "path" if change["name"] == "v_model" else "valid"
        value = change["new"]

        tmp_recipe_paths = deepcopy(self.recipe_paths)

        # Update the appropriate value
        tmp_recipe_paths[recipe_id][value_name] = value

        self.recipe_paths = tmp_recipe_paths
