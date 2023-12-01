from typing import Optional, Union

from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

import component.parameter as cp
from component.model import BenefitModel, ConstraintModel, CostModel
from component.model.aoi_model import SeplanAoi
from component.widget import custom_widgets as cw
from component.widget.alert_state import Alert

from .benefit_dialog import BenefitDialog
from .benefit_row import BenefitRow
from .constraint_dialog import ConstraintDialog
from .constraint_row import ConstraintRow
from .cost_dialog import CostDialog
from .cost_row import CostRow
from .preview_map_dialog import PreviewMapDialog

__all__ = ["Table"]


class Table(sw.Layout):
    aoi_model: Optional[SeplanAoi]
    """seplan custom aoi model. It is optional because this table is shared by the three 
    different themes we only need it in constraints."""

    def __init__(
        self,
        model: Union[BenefitModel, ConstraintModel, CostModel],
        alert: Alert,
        aoi_model: SeplanAoi,
    ) -> None:
        self.model = model
        self.alert = alert
        self.aoi_model = aoi_model

        if isinstance(model, BenefitModel):
            type_ = "benefit"
            self.Row = BenefitRow
            self.dialog = BenefitDialog(model=model, alert=self.alert)

        elif isinstance(model, ConstraintModel):
            type_ = "constraint"
            self.Row = ConstraintRow
            self.dialog = ConstraintDialog(model=model, alert=self.alert)

        elif isinstance(model, CostModel):
            type_ = "cost"
            self.Row = CostRow
            self.dialog = CostDialog(model=model, alert=self.alert)

        self.toolbar = cw.ToolBar(model, self.dialog, self.aoi_model, self.alert)
        self.preview_map = PreviewMapDialog()

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

        self.children = [self.dialog, self.preview_map, self.toolbar, self.table]

        # set rows everytime the feature collection is updated on aoitile
        self.model.observe(self.set_rows, "updated")

        # This will only happen with the constraints table
        if self.aoi_model:
            self.aoi_model.observe(self.set_rows, "feature_collection")

    @sd.catch_errors()
    def set_rows(self, *args):
        """Add, remove or update rows in the table."""
        # We don't want to recreate all the elements of the table each time. That's too expensive (specially the set_limits method)
        print("setting rows")
        view_ids = [row.layer_id for row in self.tbody.children]
        model_ids = self.model.ids

        new_ids = [id_ for id_ in model_ids if id_ not in view_ids]
        old_ids = [id_ for id_ in view_ids if id_ not in model_ids]
        edited_id = (
            self.dialog.w_id.v_model if self.dialog.w_id.v_model in view_ids else False
        )
        # Add new rows from the model
        if new_ids:
            print("new IDs")
            for new_id in new_ids:
                try:
                    row = self.Row(
                        self.model,
                        new_id,
                        self.dialog,
                        aoi_model=self.aoi_model,
                        alert=self.alert,
                        preview_map=self.preview_map,
                    )
                except Exception as e:
                    # remove the asset from the model if it fails
                    self.model.remove(new_id, update=False)
                    raise e

                self.tbody.children = [*self.tbody.children, row]
        # Remove rows
        elif old_ids:
            print("old ID")
            for old_id in old_ids:
                row_to_remove = self.tbody.get_children(attr="layer_id", value=old_id)[
                    0
                ]
                self.tbody.children = [
                    row for row in self.tbody.children if row != row_to_remove
                ]
        elif edited_id:
            print("edited ID")
            if edited_id:
                row_to_edit = self.tbody.get_children(attr="layer_id", value=edited_id)[
                    0
                ]
                row_to_edit.update_view()

        # This will be triggered the first time and every time update is modified
        # without a real change.
        elif not (new_ids or old_ids or edited_id):
            print("no ID")
            rows = [
                self.Row(
                    self.model,
                    layer_id,
                    self.dialog,
                    aoi_model=self.aoi_model,
                    alert=self.alert,
                    preview_map=self.preview_map,
                )
                for layer_id in self.model.ids
            ]
            self.tbody.children = rows
