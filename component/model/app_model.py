from traitlets import Bool, HasTraits, Int, Unicode, observe
import logging

logger = logging.getLogger("SEPLAN")


class AppModel(HasTraits):
    new_changes = Int().tag(sync=True)
    """A counter that is incremented every time any of the app model changes. Or reset to 0 when the app is saved"""

    ready = Bool(0).tag(sync=True)
    """A flag that is set to True when the app is ready to be used. It will be listebed by the drawers"""

    active_drawer = Unicode("").tag(sync=True)
    """The id of the active drawer item"""

    recipe_name = Unicode("", allow_none=True).tag(sync=True)
    """The name of the current recipe"""

    on_save = Int().tag(sync=True)
    """A counter that is incremented every time the recipe is saved. Useful to trigger the save button"""

    close_all_dialogs = Int().tag(sync=True)
    """A counter that is incremented by the drawers to close all the dialogs"""

    @observe(
        "new_changes",
        "ready",
        "active_drawer",
        "recipe_name",
        "on_save",
        "close_all_dialogs",
    )
    def log_changes(self, _):
        logger.debug(
            f"AppModel changes: {self.new_changes}, {self.ready}, {self.active_drawer}, {self.recipe_name}, {self.on_save}, {self.close_all_dialogs}"
        )
