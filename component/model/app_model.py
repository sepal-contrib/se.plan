from traitlets import Bool, HasTraits, Int


class AppModel(HasTraits):
    model_changed = Int(0).tag(sync=True)
    """A counter that is incremented every time any of the app model changes."""

    ready = Bool(0).tag(sync=True)
    """A flag that is set to True when the app is ready to be used. It will be listebed by the drawers"""
