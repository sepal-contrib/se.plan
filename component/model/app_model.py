from traitlets import Bool, HasTraits, Int, Unicode


class AppModel(HasTraits):
    new_changes = Int().tag(sync=True)
    """A counter that is incremented every time any of the app model changes. Or reset to 0 when the app is saved"""

    ready = Bool(0).tag(sync=True)
    """A flag that is set to True when the app is ready to be used. It will be listebed by the drawers"""

    active_drawer = Unicode("").tag(sync=True)
    """The id of the active drawer item"""

    recipe_name = Unicode("", allow_none=True).tag(sync=True)
    """The name of the current recipe"""
