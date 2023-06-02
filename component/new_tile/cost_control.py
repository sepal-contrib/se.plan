from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from traitlets import Unicode
from sepal_ui.scripts import decorator as sd

from component import new_widget as cw
from component import new_model as cmod


class CostView(sw.Tile):
    def __init__(self, model: cmod.CostModel):

        # set the model as a member
        self.model = model

        # create the dialog
        self.dialog = cw.CostDialog(model)

        self.w_new = sw.Btn("New Cost", "fa-solid fa-plus", small=True)
        self.w_validate = sw.Btn(
            "validate", "fa-solid fa-check", small=True, class_="ml-1"
        )
        table = cw.CostTable(self.model, self.dialog)
        row = sw.Row(
            children=[sw.Spacer(), self.w_new, self.w_validate], class_="my-2 mx-1"
        )

        super().__init__("nested", "costs", [row, table, self.dialog])

        # add js behaviour
        self.w_new.on_event("click", self.open_new_dialog)
        self.w_validate.on_event("click", self.validate)

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
        )

    def validate(self, *args):
        self.model.validated += 1


class CostControl(sm.MenuControl):
    def __init__(self, m: sm.SepalMap, model: cmod.CostModel, **kwargs):
        self.view = CostView(model)
        super().__init__(icon_content="CST", card_content=self.view, m=m, **kwargs)
        self.set_size(None, "80vw", None, "80vh")
        model.observe(lambda *_: setattr(self.menu, "v_model", False), "validated")
