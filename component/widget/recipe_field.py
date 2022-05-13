from sepal_ui import sepalwidgets as sw


class RecipeTextField(sw.TextField):
    """
    preformated textfield design to display information in the compute resume
    """

    def __init__(self, color, name, asset_name):

        super().__init__(
            small=True,
            hint=asset_name,
            persistent_hint=True,
            color=color,
            readonly=True,
            v_model=name,
        )


class RecipeIcon(sw.Icon):
    """
    preformated Icon design to display information in the compute resume
    """

    def __init__(self, color, icon):

        super().__init__(
            class_="ml-2",
            color=color,
            children=[icon],
        )
