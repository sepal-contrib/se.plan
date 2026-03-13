from pathlib import Path
from typing import Literal, Optional

from traitlets import Bool, Float, Int, Unicode, Instance, Union, List
import ipyvuetify as v
from ipywidgets import DOMWidget
from ipywidgets.widgets.widget import widget_serialization

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

        super().open_dialog()


class MapDialog(v.VuetifyTemplate):
    children = List(Union([Instance(DOMWidget), Unicode()])).tag(
        sync=True, **widget_serialization
    )

    template_file = Unicode(str(Path(__file__).parent / "vue/dialog.vue")).tag(
        sync=True
    )
    show = Bool(False).tag(sync=True)
    max_width = Union([Unicode(), Float()], default_value=None, allow_none=True).tag(
        sync=True
    )
    min_width = Union([Unicode(), Float()], default_value=None, allow_none=True).tag(
        sync=True
    )
    persistent = Bool(False).tag(sync=True)
    retain_focus = Bool(False).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def open_dialog(self, *_):
        """Open dialog."""

        self.show = True

    def close_dialog(self, *_):
        """Close dialog."""
        self.show = False
