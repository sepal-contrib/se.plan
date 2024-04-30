from sepal_ui import model
from traitlets import Int


class DashboardModel(model.Model):

    reset_count = Int(0).tag(sync=True)

    def reset(self):
        """Reset the model to its default values."""
        self.reset_count += 1
