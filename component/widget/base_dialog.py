import sepal_ui.sepalwidgets as sw


class BaseDialog(sw.Dialog):
    def __init__(self, *args, **kwargs):
        kwargs["persistent"] = kwargs.get("persistent", True)
        kwargs["v_model"] = kwargs.get("v_model", False)
        kwargs["max_width"] = kwargs.get("max_width", "700px")

        super().__init__(*args, **kwargs)

    def open(self, *_):
        """Open dialog."""
        self.v_model = True

    def close(self, *_):
        """Close dialog."""
        self.v_model = False
