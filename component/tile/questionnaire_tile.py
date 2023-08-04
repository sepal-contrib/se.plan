import sepal_ui.sepalwidgets as sw

import component.parameter as cp
from component.message import cm
from component.model import BenefitModel, ConstraintModel, CostModel
from component.model.recipe import Recipe
from component.widget.custom_widgets import Tabs
from component.widget.questionaire_table import Table


class QuestionnaireTile(sw.Tile):
    def __init__(self, recipe: Recipe):
        # name the tile
        title = cm.questionnaire_title
        id_ = "questionnaire_widget"

        self.constraint_model = ConstraintModel()
        self.benefit_model = BenefitModel()
        self.cost_model = CostModel()

        benefit_table = Table(model=recipe.benefit_model)
        constraint_table = Table(
            model=recipe.constraint_model, aoi_model=recipe.seplan_aoi.aoi_model
        )
        cost_table = Table(model=recipe.cost_model)

        tabs = Tabs(
            titles=[cm[theme].tab_title for theme in cp.themes],
            content=[benefit_table, constraint_table, cost_table],
            class_="mt-5",
            fixed_tabs=True,
            centered=True,
        )

        super().__init__(id_, title, inputs=[tabs])
