from sepal_ui import sepalwidgets as sw


class SimpleRangeSlider(sw.RangeSlider):
    def __init__(self, **kwargs) -> None:
        """Simple Slider is a simplified slider that can be center alined in table.
        The normal vuetify slider is included html placeholder for the thumbs and the messages (errors and hints). This is preventing anyone from center-aligning them in a table. This class is behaving exactly like a regular Slider but embed extra css class to prevent the display of these sections. any hints or message won't be displayed.
        """
        super().__init__(**kwargs)
        self.class_list.add("v-no-messages")
