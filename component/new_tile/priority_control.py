from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from traitlets import Unicode
from sepal_ui.scripts import decorator as sd

from component import new_widget as cw
from component import new_model as cmod


class PriorityView(sw.Tile):
    def __init__(self, model: cmod.PriorityModel):

        # set the model as a member
        self.model = model

        # create the dialog
        self.dialog = cw.PriorityDialog(model)

        self.w_new = sw.Btn(
            "New Priority", "fa-solid fa-plus", small=True, type_="success"
        )
        table = cw.PriorityTable(self.model, self.dialog)
        row = sw.Row(children=[sw.Spacer(), self.w_new], class_="my-2 mx-1")

        super().__init__("nested", "priorities", [row, table, self.dialog])

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


class PriorityControl(sm.MenuControl):
    def __init__(self, m: sm.SepalMap, model: cmod.PriorityModel, **kwargs):
        self.view = PriorityView(model)
        super().__init__(icon_content="BEN", card_content=self.view, m=m, **kwargs)
        self.set_size(None, "80vw", None, "80vh")
