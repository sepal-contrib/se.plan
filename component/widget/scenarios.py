"""UI component widget to compare different scenarios."""

# I have to define a dialog which can add multiple scenarios from recipies
# the UI should look like a the .this scenario and an option to add up to 3 more
# a new scenario can be uploaded in the form of recipies, and therefore,
# I can use a fileInput component.
# Once the user has added the scenarios, the component should validate the scenarios:
# Base on the rule that they can only be compared if they have the same main AOI.
# If the scenarios are valid, I can recipe.load() and store the scenarios a.k.a. the recipies
# in a dictionary? or a list? and then I can use the compare()

# Later, I can use this component to be used in two specific tiles, the map tile and the
# Dashboard tile.

# Map Tile.

# User clicks on the comparision button that is located in the toolbar of the map tile.
# The map tile will open a dialog with the scenarios component.
# The user can add up to 4 scenarios.
# The user validates the scenarios.
# The user clicks on the compare button.
# This compare button will automatically create the suitability index for each of the scenarios...
# And then it will add them to the map...

# So the component has to have a method called compare() which creates the suitability maps for each
# of the scenarios, as EE objects (without computing them), and then, a method that can be named as
# compare_layers() which will add the suitability maps to the map, which of course has to receive
# a map object, actually it can be any map.


# Dashboard Tile.

# The logic will be the same, the only difference is that the method to be called has to be named
# as compare_statistics() which will create the charts for each of the scenarios, and.... a placeholder??? from the tile... yes.... Ideally I would also use this component independetly.
# This method has to accept two ipyvuetify like containers, one for the main plots and the other for the layer plots.
# The method would be something like: compare_statistics(main_container, layer_container) and then the method will add the plots to the containers, if there's no container, it will just create one... So in that way we are safe to use this component outside the tool.


from component.scripts.statistics import get_summary_statistics
from component.widget.base_dialog import BaseDialog
import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from component.widget.custom_widgets import TextBtn
from component.model.recipe import Recipe
import component.parameter as cp


class CompareScenariosDialog(BaseDialog):
    """Dialog to compare multiple scenarios from recipes."""

    def __init__(self):
        super().__init__()
        self.recipes = []
        self.scenario_inputs = []
        self.suitability_indices = []
        self.create_ui()

    def create_ui(self):
        # Create UI elements for up to 4 scenario inputs
        self.scenario_inputs = [
            sw.FileInput(".json", folder=cp.result_dir, root=cp.result_dir)
            for _ in range(4)
        ]
        self.btn_validate = TextBtn("Validate Scenarios")
        self.btn_compare = TextBtn("Compare")
        self.btn_cancel = TextBtn("Cancel", outlined=True)

        # Assemble the layout
        scenario_inputs_layout = v.Layout(children=self.scenario_inputs, class_="pa-4")
        self.children = [
            v.Card(
                class_="pa-4",
                children=[
                    sw.CardTitle(children=["Compare Scenarios"]),
                    sw.CardText(children=[scenario_inputs_layout]),
                    sw.CardActions(
                        children=[
                            sw.Spacer(),
                            self.btn_validate,
                            self.btn_compare,
                            self.btn_cancel,
                        ]
                    ),
                ],
            )
        ]

        # Set up event handlers
        self.btn_validate.on_event("click", self.validate_scenarios)
        self.btn_compare.on_event("click", self.compare)
        self.btn_cancel.on_event("click", self.cancel)

    def validate_scenarios(self, *args):
        """Validate that all selected scenarios have the same AOI."""
        self.recipes = []
        aois = []
        for input_widget in self.scenario_inputs:
            recipe_path = input_widget.v_model
            if recipe_path:
                try:
                    recipe = Recipe()
                    recipe.load(recipe_path)
                    self.recipes.append(recipe)
                    aois.append(recipe.seplan_aoi.aoi_model)
                except Exception as e:
                    # Handle invalid recipe file
                    v.Dialog(
                        children=[v.Alert(type="error", children=[str(e)])]
                    ).open = True
                    return

        if not aois:
            v.Dialog(
                children=[v.Alert(type="warning", children=["No scenarios selected."])]
            ).open = True
            return

        # Check that all AOIs are the same
        first_aoi = aois[0]
        if all(aoi == first_aoi for aoi in aois):
            # Validation successful
            v.Dialog(
                children=[
                    v.Alert(
                        type="success", children=["Scenarios validated successfully."]
                    )
                ]
            ).open = True
            self.btn_compare.disabled = False
        else:
            # Show an error message
            v.Dialog(
                children=[
                    v.Alert(
                        type="error", children=["AOIs do not match across scenarios."]
                    )
                ]
            ).open = True
            self.btn_compare.disabled = True

    def compare(self, *args):
        """Compute suitability indices for each scenario."""
        self.suitability_indices = []
        for recipe in self.recipes:
            try:
                index = recipe.seplan.get_benefit_index()
                self.suitability_indices.append(index)
            except Exception as e:
                v.Dialog(children=[v.Alert(type="error", children=[str(e)])]).open = (
                    True
                )
                return
        # Proceed to add layers or compute statistics as needed

    def compare_layers(self, map_obj):
        """Add suitability indices as layers to the map."""
        for idx, index in enumerate(self.suitability_indices):
            layer_name = f"Scenario {idx + 1} Suitability"
            map_obj.add_layer(index, {}, layer_name)

    def compare_statistics(self, main_container=None, layer_container=None):
        """Compute and display summary statistics."""
        if main_container is None:
            main_container = v.Container()
        if layer_container is None:
            layer_container = v.Container()

        for idx, recipe in enumerate(self.recipes):
            stats = get_summary_statistics(recipe.seplan)
