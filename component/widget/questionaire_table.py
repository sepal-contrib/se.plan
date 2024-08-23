from typing import Optional, Union

from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd

import component.parameter as cp
from component.model import BenefitModel, ConstraintModel, CostModel
from component.model.aoi_model import SeplanAoi
from component.scripts.logger import logger
from component.widget import custom_widgets as cw
from component.widget.alert_state import Alert
from component.widget.preview_theme_btn import PreviewThemeBtn

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
        preview_map: PreviewMapDialog = None,
        preview_theme_map_btn: PreviewThemeBtn = "",
    ) -> None:
        self.model = model
        self.alert = alert or Alert()
        self.aoi_model = aoi_model
        self.preview_map = preview_theme_map_btn

        if isinstance(model, BenefitModel):
            self.type_ = "benefit"
            self.Row = BenefitRow
            self.dialog = BenefitDialog(model=model, alert=self.alert)

        elif isinstance(model, ConstraintModel):
            self.type_ = "constraint"
            self.Row = ConstraintRow
            self.dialog = ConstraintDialog(model=model, alert=self.alert)

        elif isinstance(model, CostModel):
            self.type_ = "cost"
            self.Row = CostRow
            self.dialog = CostDialog(model=model, alert=self.alert)

        else:
            raise ValueError(
                f"model should be an instance of BenefitModel, ConstraintModel or CostModel, not {type(model)}"
            )

        self.preview_map = preview_map or PreviewMapDialog()
        self.toolbar = cw.ToolBar(
            model,
            self.dialog,
            self.aoi_model,
            self.alert,
            preview_theme_map_btn,
        )

        # create the table
        super().__init__()

        self.class_ = "d-block"

        # generate header using the translator
        headers = sw.Html(
            tag="tr",
            children=[
                sw.Html(tag="th", children=[title])
                for title in cp.table_headers[self.type_].values()
            ],
        )

        self.tbody = sw.Html(tag="tbody", children=[])
        self.set_rows(_v="init")

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
        self.model.observe(lambda *x: self.set_rows(_v="obs"), "updated")

    @sd.catch_errors()
    def set_rows(self, _v, *args):
        """Add, remove or update rows in the table."""
        # We don't want to recreate all the elements of the table each time. That's too expensive (specially the set_limits method)
        logger.info(f"setting rows from: {_v}")
        view_ids = [row.layer_id for row in self.tbody.children]
        model_ids = self.model.ids
        logger.info("Current model IDs", model_ids)
        logger.info("Current view IDs", view_ids)

        new_ids = [id_ for id_ in model_ids if id_ not in view_ids]
        old_ids = [id_ for id_ in view_ids if id_ not in model_ids]

        logger.info("new IDs", new_ids)
        logger.info("old IDs", old_ids)

        edited_id = (
            self.dialog.w_id.v_model if self.dialog.w_id.v_model in view_ids else False
        )
        # Add new rows from the model
        if new_ids:
            logger.info("new IDs")
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
        if old_ids:
            logger.info("old ID")
            for old_id in old_ids:
                row_to_remove = self.tbody.get_children(attr="layer_id", value=old_id)[
                    0
                ]
                # unobserve the row to avoid ghost listeners
                if self.type_ == "constraint":
                    row_to_remove.unobserve_all()

                self.tbody.children = [
                    row for row in self.tbody.children if row != row_to_remove
                ]
        if edited_id:
            logger.info("edited ID")
            if edited_id:
                row_to_edit = self.tbody.get_children(attr="layer_id", value=edited_id)[
                    0
                ]
                row_to_edit.update_view()

        # This will be triggered the first time and every time update is modified
        # without a real change.
        elif not (new_ids or old_ids or edited_id):
            logger.info("no ID")

            # let's first unobserve all the previou rows
            if self.type_ == "constraint":
                for row in self.tbody.children:
                    logger.info("unobserving row")
                    row.unobserve_all()

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
