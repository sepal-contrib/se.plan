"""Dialog to display invalid data from benefits, constraints and costs."""

from pathlib import Path
from typing import Callable, List, Optional

import sepal_ui.sepalwidgets as sw
from traitlets import List as TraitsList, Unicode
import logging

logger = logging.getLogger("SEPLAN.component.widget.invalid_data_dialog")


class InvalidDataDialog(sw.Dialog):
    """Dialog that displays invalid data found during recipe loading.

    Inherits from sepal_ui Dialog which provides open_dialog() and close_dialog() methods.

    Usage:
        dialog = InvalidDataDialog(on_continue_callback=..., on_cancel_callback=...)
        dialog.show_errors(benefits_errors=..., constraints_errors=..., costs_errors=...)
    """

    # Point to the Vue template file
    template_file = Unicode(
        str(Path(__file__).parent / "vue" / "invalidDataDialog.vue")
    ).tag(sync=True)

    # Lists of error dicts for each section. Kept generic and serializable.
    benefits = TraitsList([]).tag(sync=True)
    constraints = TraitsList([]).tag(sync=True)
    costs = TraitsList([]).tag(sync=True)

    # Optional small message to show in alert area
    alert = Unicode(allow_none=True).tag(sync=True)

    def __init__(
        self,
        on_continue_callback: Optional[Callable] = None,
        on_cancel_callback: Optional[Callable] = None,
        **kwargs,
    ):
        # Set dialog properties
        kwargs.setdefault("max_width", 800)
        kwargs.setdefault("persistent", True)

        super().__init__(**kwargs)

        self.on_continue_callback = on_continue_callback
        self.on_cancel_callback = on_cancel_callback

    def show_errors(
        self,
        benefits_errors: Optional[List[dict]] = None,
        constraints_errors: Optional[List[dict]] = None,
        costs_errors: Optional[List[dict]] = None,
    ) -> None:
        """Populate the dialog with errors and open it.

        The lists are copied to the traits so they sync to the Vue frontend.
        If a section has no errors (None or empty) it will be hidden in the UI.
        """
        logger.debug("Showing InvalidDataDialog with errors")
        self.benefits = benefits_errors or []
        self.constraints = constraints_errors or []
        self.costs = costs_errors or []

        # clear any previous alert
        self.alert = ""

        # open dialog using inherited method
        self.open_dialog()

    # Vue-callable methods (prefix 'vue_')
    def vue_on_continue(self, data=None):
        """Called from Vue when the user clicks Continue.

        This will close the dialog and call the optional callback so the
        backend can do any logging/cleanup. The actual model state is
        expected to already reflect the cleaned data.

        Args:
            data: Event data from Vue (unused but required by ipyvue)
        """
        self.close_dialog()
        if callable(self.on_continue_callback):
            try:
                self.on_continue_callback()
            except Exception:
                # avoid raising in the widget; backend should handle errors
                pass

    def vue_on_cancel(self, data=None):
        """Called from Vue when the user clicks Cancel.

        This closes the dialog and invokes the cancel callback which should
        reset the application's models to defaults.

        Args:
            data: Event data from Vue (unused but required by ipyvue)
        """
        self.close_dialog()
        if callable(self.on_cancel_callback):
            try:
                self.on_cancel_callback()
            except Exception:
                pass
