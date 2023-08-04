"""questionnaire model that sets the basic structure for theme model."""

from sepal_ui import model
from traitlets import Int


class QuestionnaireModel(model.Model):
    updated = Int(0).tag(sync=True)

    def import_data(self, data: dict):
        """Set the data for each of the model traits and trigger the update."""
        self.import_data(data)
        self.updated += 1

    def get_index(self, id: str) -> int:
        """get the index of the searched layer id."""
        return next(i for i, v in enumerate(self.ids) if v == id)
