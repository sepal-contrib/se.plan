import solara_
from solara.lab import headers
import ipyvuetify as v
from sepal_ui import color


@solara_.component
def Page():
    print(headers.value)

    solara_.lab.theme.themes.light.primary = "#5BB624"
    solara_.lab.theme.themes.dark.primary = "#76591e"
    solara_.lab.theme.dark = color._dark_theme

    v.Btn.element(
        children=["this is a test", f" - theme: {headers.value}"],
        color="primary",
    )
