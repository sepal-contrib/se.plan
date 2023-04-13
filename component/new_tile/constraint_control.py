from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from sepal_ui.aoi import AoiModel
from traitlets import Unicode
from sepal_ui.scripts import decorator as sd

from component import new_widget as cw
from component import new_model as cmod


class ConstraintView(sw.Tile):
    def __init__(self, model: cmod.ConstraintModel, aoi_model: AoiModel):

        # create the dialog
        self.dialog = cw.ConstraintDialog(model)

        self.w_new = sw.Btn(
            "New Constraint", "fa-solid fa-plus", small=True, type_="success"
        )
        table = cw.ConstraintTable(model, self.dialog, aoi_model)
        row = sw.Row(children=[sw.Spacer(), self.w_new], class_="my-2 mx-1")

        super().__init__("nested", "constraints", [row, table, self.dialog])

        # add js behaviour
        self.w_new.on_event("click", self.open_new_dialog)

    @sd.switch("loading", on_widgets=["dialog"])
    def open_new_dialog(self, *args) -> None:
        """open the new priority dialog"""

        self.dialog.value = True

        self.dialog.fill(
            None,
            None,
            None,
            None,
            None,
            None,
        )


class ConstraintControl(sm.MenuControl):
    def __init__(
        self, m: sm.SepalMap, model: cmod.ConstraintModel, aoi_model: AoiModel, **kwargs
    ):
        self.view = ConstraintView(model, aoi_model)
        super().__init__(icon_content="CNT", card_content=self.view, m=m, **kwargs)
        self.set_size(None, "80vw", None, "80vh")
