"""questionnaire model to store the questionnaire data."""

from sepal_ui import model
from traitlets import Any


class QuestionnaireModel(model.Model):
    """Store the questionnaire data."""

    constraints = Any("").tag(sync=True)
    priorities = Any("").tag(sync=True)
    recipe_name = Any("").tag(sync=True)
