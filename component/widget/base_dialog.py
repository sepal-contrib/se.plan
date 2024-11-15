from typing import Literal, Optional
import sepal_ui.sepalwidgets as sw
from component.message import cm


class BaseDialog(sw.Dialog):
    def __init__(self, *args, **kwargs):
        kwargs["persistent"] = kwargs.get("persistent", True)
        kwargs["v_model"] = kwargs.get("v_model", False)
        kwargs["max_width"] = kwargs.get("max_width", "700px")

        super().__init__(*args, **kwargs)

    def open_dialog(self, *_, type_: Optional[Literal["add", "save"]] = None):
        """Open dialog."""

        if type_:
            self.get_children(attr="id", value="dialog_action")[0].msg = cm.dialog.btn[
                type_
            ]

        self.v_model = True

    def close_dialog(self, *_):
        """Close dialog."""
        self.v_model = False
