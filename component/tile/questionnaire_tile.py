import sepal_ui.sepalwidgets as sw
from sepal_ui.aoi.aoi_model import AoiModel

import component.parameter as cp
from component.message import cm
from component.model import BenefitModel, ConstraintModel, CostModel
from component.widget.custom_widgets import Tabs
from component.widget.questionaire_table import Table


class QuestionnaireTile(sw.Tile):
    def __init__(self):
        # name the tile
        title = cm.questionnaire_title
        id_ = "questionnaire_widget"

        # TODO: Change for real one once we tested this
        aoi_model = AoiModel(admin="959")
        constraint_model = ConstraintModel()
        benefit_model = BenefitModel()
        cost_model = CostModel()

        benefit_table = Table(model=benefit_model)
        constraint_table = Table(model=constraint_model, aoi_model=aoi_model)
        cost_table = Table(model=cost_model)

        tabs = Tabs(
            titles=[cm[theme].tab_title for theme in cp.themes],
            content=[benefit_table, constraint_table, cost_table],
            class_="mt-5",
            fixed_tabs=True,
            centered=True,
        )

        # build the tile
        super().__init__(id_, title, inputs=[tabs])
