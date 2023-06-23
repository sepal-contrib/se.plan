from sepal_ui import sepalwidgets as sw

from component import new_widget as cw


class PriorityView(sw.Tile):
    def __init__(self):

        self.w_new = sw.Btn("New Priority", "fa-solid fa-plus", small=True)
        table = cw.PriorityTable()
        row = sw.Row(children=[sw.Spacer(), self.w_new], class_="my-2 mx-1")

        super().__init__("nested", "priorities", [row, table])


class CostView(sw.Tile):
    def __init__(self):

        super().__init__("nested", "cost")


class ConstraintView(sw.Tile):
    def __init__(self):

        super().__init__("nested", "constraints")


class QuestionView(sw.Tile):
    def __init__(self):

        # set the map

        # set the layer controls

        # The 3 managers to  install in the panel

        super().__init__("nested", "questionaire")
