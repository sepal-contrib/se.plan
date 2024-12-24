import solara
from solara.lab import headers
import ipyvuetify as v
from sepal_ui import color

solara.server.settings.assets.fontawesome_path = "/font-awesome/6.2.1/css/all.min.css"
solara.server.settings.assets.extra_locations = ["./assets/"]
solara.settings.assets.cdn = "https://cdnjs.cloudflare.com/ajax/libs/"
import ipyvuetify as v

solara.server.settings.assets.fontawesome_path = "/font-awesome/6.2.1/css/all.min.css"
solara.server.settings.assets.extra_locations = ["./assets/"]
solara.settings.assets.cdn = "https://cdnjs.cloudflare.com/ajax/libs/"


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
