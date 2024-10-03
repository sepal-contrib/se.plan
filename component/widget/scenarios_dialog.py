"""UI component widget to compare different scenarios."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from typing import List
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


class ScenarioInputs(sw.Layout):
    """Returns a widget that can add dinamically fileInputs."""

    recipe_paths: RecipePaths = Dict({}).tag(sync=True)
    """Dicionary of recipe paths."""

    idx = Int(0).tag(sync=True)

    limited_reached = Int(0).tag(sync=True)
    "will be increased when user tries to add more inputs than the limit."

    def __init__(self, main_recipe: Recipe = None, recipe_limit=4):

        self.class_ = "d-block"
        self.recipe_limit = recipe_limit

        super().__init__()

        # Add btn
        btn_add = IconBtn("mdi-plus", color="primary", class_="mr-2")
        btn_add.on_event("click", self.add_input)
        main_recipe = self.get_input_row(trashable=False, main_recipe=main_recipe)

        headers = sw.Html(
            tag="tr",
            children=[
                sw.Html(tag="th", children=["Action"]),
                sw.Html(
                    tag="th",
                    children=[v.Layout(children=["Recipe", v.Spacer(), btn_add])],
                ),
            ],
        )

        self.tbody = sw.Html(
            attributes={"id": "tbody"},
            tag="tbody",
            children=[main_recipe, self.get_input_row(trashable=False)],
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

        remove_btn = TableIcon("mdi-trash-can", name="trash", disabled=not trashable)

        if trashable:
            remove_btn.on_event("click", lambda *args: self.remove_input_row(row_id))

        file_input = RecipeInput(attributes={"id": row_id}, default_recipe=main_recipe)

        file_input.observe(self.update_recipe_paths, ["v_model", "valid"])

        # Set the structure of the recipe_paths
        row_info: RecipeInfo = {"path": file_input.v_model, "valid": False}
        self.recipe_paths.setdefault(row_id, row_info)
        self.idx += 1

        return sw.Html(
            tag="tr",
            attributes={"id": row_id},
            children=[
                sw.Html(style_="width: 65px", tag="td", children=[remove_btn]),
                sw.Html(tag="td", children=[file_input]),
            ],
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


class CompareScenariosDialog(BaseDialog):
    """Dialog to compare multiple scenarios from recipes."""

    def __init__(
        self, map_: SepalMap = None, alert: Alert = None, recipe: Recipe = None
    ):
        super().__init__()

        self.map_ = map_
        self.alert = alert or Alert()

        self.recipes: List[Recipe] = []
        self.scenario_inputs = []
        self.suitability_indices = []

        # Create UI elements for up to 2 scenario inputs
        self.scenario_inputs = ScenarioInputs(
            main_recipe=recipe if recipe else None,
            recipe_limit=2,
        )
        self.btn_compare = TextBtn("Compare")
        self.btn_cancel = TextBtn("Cancel", outlined=True)

        # Assemble the layout
        scenario_inputs_layout = v.Layout(
            children=[self.scenario_inputs], class_="pa-0 ma-0"
        )
        self.children = [
            v.Card(
                class_="ma-0 ",
                children=[
                    sw.CardTitle(children=["Compare Scenarios"]),
                    sw.CardText(children=[scenario_inputs_layout]),
                    sw.CardActions(
                        children=[
                            sw.Spacer(),
                            self.btn_compare,
                            self.btn_cancel,
                        ]
                    ),
                ],
            )
        ]

        self.compare_layers = loading_button(self.alert, self.btn_compare)(
            self.compare_layers
        )
        self.btn_compare.on_event("click", self.compare_layers)
        self.btn_cancel.on_event("click", self.close_dialog)

    def validate_scenarios(self):
        """Validate that all selected scenarios have the same AOI."""

        # First validate that all of them are valid
        validate_scenarios_recipes(self.scenario_inputs.recipe_paths)
        are_comparable(self.scenario_inputs.recipe_paths)

    def compare_layers(self, widget, event, data, map_: SepalMap = None):
        """Add suitability indices as layers to the map."""

        map_ = map_ or self.map_

        # Remove previous layer controls
        map_.controls = [
            control
            for control in map_.controls
            if not isinstance(control, SplitMapControl)
        ]

        recipes = []
        self.validate_scenarios()

        for _, recipe_data in self.scenario_inputs.recipe_paths.items():
            recipe_path = recipe_data["path"]
            print(recipe_path)
            recipe = Recipe()
            recipe.load(recipe_path)
            recipes.append(recipe)

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

    def compare_statistics(self, main_container=None, layer_container=None):
        """Compute and display summary statistics."""
        if main_container is None:
            main_container = v.Container()
        if layer_container is None:
            layer_container = v.Container()

        for idx, recipe in enumerate(self.recipes):
            stats = get_summary_statistics(recipe.seplan)
