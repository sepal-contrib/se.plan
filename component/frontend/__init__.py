# load custom styling of sepal_ui
from pathlib import Path

from IPython.display import HTML, display

# get the path  to the custom css
CSS_DIR = Path(__file__).parent
custom_css = HTML(f"<style>{(CSS_DIR / 'custom.css').read_text()}</style>")
display(custom_css)
