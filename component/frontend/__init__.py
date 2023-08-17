# load custom styling of sepal_ui
from pathlib import Path

import ipyvuetify as v
from IPython.display import display

# get the path  to the custom css
CSS_DIR = Path(__file__).parent
custom_css = v.Html(tag="style", children=[(CSS_DIR / "custom.css").read_text()])
display(custom_css)
