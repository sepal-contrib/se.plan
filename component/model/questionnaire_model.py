"""questionnaire model that sets the basic structure for theme model."""

from sepal_ui import model
from traitlets import Int


class QuestionnaireModel(model.Model):
    updated = Int(0).tag(sync=True)

    new_changes = Int().tag(sync=True)
    """A counter that is incremented every time any trait of the model changes. This trait is linked to the recipe model and later with app_model, so we can show messaages on the app_bar"""

    def import_data(self, data: dict):
        """Set the data for each of the model traits and triggers the update of the view."""
        super().import_data(data)
        self.updated += 1

        self.new_changes += 1

    def get_index(self, id: str) -> int:
        """get the index of the searched layer id."""
        print("getting index", id)
        return next(i for i, v in enumerate(self.ids) if v == id)
