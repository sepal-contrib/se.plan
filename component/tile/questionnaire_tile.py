from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component.message import cm
from component import widget as cw
from .constraints_tile import ConstraintTile
from .priority_tile import PriorityTile
from .cost_tile import CostTile


class QuestionnaireTile(sw.Tile):
    def __init__(self, question_model, layer_model, aoi_view):

        # name the tile
        title = cm.questionnaire.title
        id_ = "questionnaire_widget"

        # build the tiles
        self.constraint_tile = ConstraintTile(aoi_view, layer_model)
        self.priority_tile = PriorityTile()
        self.cost_tile = CostTile(aoi_view, layer_model)

        self.tiles = [self.constraint_tile, self.priority_tile, self.cost_tile]

        # build the content and the stepper header
        tab_content = []
        for i, tile in enumerate(self.tiles):

            # add the title and content
            tab_content.append(v.Tab(children=[tile.get_title()]))
            tab_content.append(v.TabItem(children=[tile]))

        # build the tabs
        tabs = tabs = v.Tabs(
            class_="mt-5", fixed_tabs=True, centered=True, children=tab_content
        )

        # create a dialog widget
        self.dialog = cw.EditDialog(aoi_view, layer_model)

        # build the tile
        super().__init__(id_, title, inputs=[self.dialog, tabs])

        # save the associated model and set the default value
        self.question_model = question_model
        self.layer_model = layer_model
        self.question_model.constraints = self.constraint_tile.custom_v_model
        self.question_model.priorities = self.priority_tile.v_model

        # js behaviours
        [
            btn.on_event("click", self._open_dialog)
            for btn in self.priority_tile.table.btn_list
        ]
        [
            c.btn.on_event("click", self._open_dialog)
            for c in self.constraint_tile.criterias
        ]
        self.constraint_tile.observe(self.__on_constraint, "custom_v_model")
        self.priority_tile.table.observe(self.__on_priority_tile, "v_model")
        self.dialog.observe(self.constraint_tile._update_constraints, "updated")

    def _open_dialog(self, widget, event, data):
        """populate and update the dialog"""

        # get the layer informations and
        self.dialog.set_dialog(widget._metadata["layer"])

        return

    def load_data(self, data):
        """load a questionnaire from a dict source"""

        # relaod the "range" constraints
        self.constraint_tile._update_constraints()

        # reload constraints
        self.constraint_tile.load_data(data.constraints)

        # reload priorities
        self.priority_tile.table.load_data(data.priorities)

        return

    def __on_constraint(self, change):
        self.question_model.constraints = change["new"]
        return

    def __on_priority_tile(self, change):
        self.question_model.priorities = change["new"]
        return
