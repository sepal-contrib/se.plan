from traitlets import Bool, HasTraits, Int, Unicode


class AppModel(HasTraits):
    model_changed = Int(0).tag(sync=True)
    """A counter that is incremented every time any of the app model changes."""

    ready = Bool(0).tag(sync=True)
    """A flag that is set to True when the app is ready to be used. It will be listebed by the drawers"""

    active_drawer = Unicode("").tag(sync=True)
    """The id of the active drawer item"""
