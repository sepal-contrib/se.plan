from typing import Optional, Union

from sepal_ui import sepalwidgets as sw
from sepal_ui.aoi import AoiModel

import component.parameter as cp
from component.model import BenefitModel, ConstraintModel, CostModel
from component.widget import custom_widgets as cw

from .benefit_dialog import BenefitDialog
from .benefit_table import BenefitRow
from .constraint_dialog import ConstraintDialog
from .constraint_table import ConstraintRow
from .cost_dialog import CostDialog
from .cost_table import CostRow


class Table(sw.Layout):
    def __init__(
        self,
        model: Union[BenefitModel, ConstraintModel, CostModel],
        aoi_model: Optional[AoiModel] = None,
    ) -> None:
        self.model = model
        self.aoi_model = aoi_model

        if isinstance(model, BenefitModel):
            type_ = "benefit"
            self.Row = BenefitRow
            self.dialog = BenefitDialog(model=model)

        elif isinstance(model, ConstraintModel):
            type_ = "constraint"
            self.Row = ConstraintRow
            self.dialog = ConstraintDialog(model=model)

        elif isinstance(model, CostModel):
            type_ = "cost"
            self.Row = CostRow
            self.dialog = CostDialog(model=model)

        self.toolbar = cw.ToolBar(model, self.dialog)

        # create the table
        super().__init__()

        self.class_ = "d-block"

        # generate header using the translator
        headers = sw.Html(
            tag="tr",
            children=[
                sw.Html(tag="th", children=[title])
                for title in cp.table_headers[type_].values()
            ],
        )

        self.tbody = sw.Html(tag="tbody", children=[])
        self.set_rows()

        # create the table
        self.table = sw.SimpleTable(
            dense=False,
            children=[
                sw.Html(tag="thead", children=[headers]),
                self.tbody,
            ],
        )

        self.children = [self.dialog, self.toolbar, self.table]

        # add js behavior
        self.model.observe(self.set_rows, "updated")

    def set_rows(self, *args):
        """Add, remove or update rows in the table."""
        # We don't want to recreate all the elements of the table each time. That's too expensive (specially the get_limits method)

        view_ids = [row.layer_id for row in self.tbody.children]
        model_ids = self.model.ids

        new_ids = [id_ for id_ in model_ids if id_ not in view_ids]
        old_ids = [id_ for id_ in view_ids if id_ not in model_ids]
        edited_id = (
            self.dialog.w_id.v_model if self.dialog.w_id.v_model in view_ids else False
        )
        if new_ids:
            for new_id in new_ids:
                row = self.Row(
                    self.model, new_id, self.dialog, aoi_model=self.aoi_model
                )
                self.tbody.children = [*self.tbody.children, row]

        elif old_ids:
            for old_id in old_ids:
                row_to_remove = self.tbody.get_children(attr="layer_id", value=old_id)[
                    0
                ]
                self.tbody.children = [
                    row for row in self.tbody.children if row != row_to_remove
                ]
        elif edited_id:
            if edited_id:
                row_to_edit = self.tbody.get_children(attr="layer_id", value=edited_id)[
                    0
                ]
                row_to_edit.update_view()

        # This will be triggered the first time and every time update is modified
        # without a real change.
        elif not (new_ids or old_ids or edited_id):
            rows = [
                self.Row(self.model, layer_id, self.dialog, aoi_model=self.aoi_model)
                for layer_id in self.model.ids
            ]
            self.tbody.children = rows
