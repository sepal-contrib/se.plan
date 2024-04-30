import sepal_ui.sepalwidgets as sw

import component.parameter as cp
from component.message import cm
from component.model.recipe import Recipe
from component.widget.alert_state import Alert, AlertDialog, AlertState
from component.widget.custom_widgets import Tabs
from component.widget.preview_map_dialog import PreviewMapDialog
from component.widget.preview_theme_btn import PreviewThemeBtn
from component.widget.questionaire_table import Table


class QuestionnaireTile(sw.Layout):
    def __init__(self):
        # name the tile
        self._metadata = {"mount_id": "questionnaire_tile"}
        self.class_ = "d-block"

        super().__init__()

    def build(self, recipe: Recipe, build_alert: AlertState):
        """Build the questionnaire tile."""
        build_alert.set_state("new", "questionnaire", "building")

        self.alert = Alert()
        alert_dialog = AlertDialog(self.alert)

        # define a reusable preview map dialog
        preview_map = PreviewMapDialog()

        benefit_table = Table(
            model=recipe.benefit_model,
            alert=self.alert,
            aoi_model=recipe.seplan_aoi,
            preview_map=preview_map,
            preview_theme_map_btn=PreviewThemeBtn(
                type_="benefit",
                map_=preview_map,
                seplan=recipe.seplan,
                alert=self.alert,
            ),
        )

        constraint_table = Table(
            model=recipe.constraint_model,
            alert=self.alert,
            aoi_model=recipe.seplan_aoi,
            preview_map=preview_map,
            preview_theme_map_btn=PreviewThemeBtn(
                type_="constraint",
                map_=preview_map,
                seplan=recipe.seplan,
                alert=self.alert,
            ),
        )

        cost_table = Table(
            model=recipe.cost_model,
            alert=self.alert,
            aoi_model=recipe.seplan_aoi,
            preview_map=preview_map,
            preview_theme_map_btn=PreviewThemeBtn(
                type_="cost",
                map_=preview_map,
                seplan=recipe.seplan,
                alert=self.alert,
            ),
        )

        tabs = Tabs(
            titles=[cm[theme].tab_title for theme in cp.themes],
            content=[benefit_table, constraint_table, cost_table],
            class_="mt-5",
            fixed_tabs=True,
            centered=True,
        )

        self.set_children([alert_dialog, preview_map] + [tabs], position="last")

        build_alert.set_state("new", "questionnaire", "done")
