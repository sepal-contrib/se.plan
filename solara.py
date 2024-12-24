import solara
from solara.lab import headers
import ipyvuetify as v
from sepal_ui import color


@solara.component
def Page():
    print(headers.value)

    solara.lab.theme.themes.light.primary = "#5BB624"
    solara.lab.theme.themes.dark.primary = "#76591e"
    solara.lab.theme.dark = color._dark_theme

    v.Btn.element(
        children=["this is a test", f" - theme: {headers.value}"],
        color="primary",
    )
