import random
import json

import pandas as pd
from sepal_ui import model
from traitlets import Any

from component import parameter as cp


class QuestionnaireModel(model.Model):
    constraints = Any("").tag(sync=True)
    priorities = Any("").tag(sync=True)
    recipe_name = Any("").tag(sync=True)
