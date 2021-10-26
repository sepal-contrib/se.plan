import os
from pathlib import Path

from sepal_ui.translator import Translator

lang = "en"
if "CUSTOM_LANGUAGE" in os.environ:
    lang = os.environ["CUSTOM_LANGUAGE"]

cm = Translator(Path(__file__).parent, lang)
