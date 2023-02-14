from sepal_ui import sepalwidgets as sw


class PriorityView(sw.Tile):
    def __init__(self):

        super().__init__("nested", "priorities")


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
