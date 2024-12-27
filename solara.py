import requests
import solara
from solara.lab import headers
import ipyvuetify as v
from sepal_ui import color
from eeclient.client import EESession
from eeclient.data import get_info
import ee

ee.Initialize()


@solara.component
def Page():
    print(headers.value)

    solara.lab.theme.themes.light.primary = "#5BB624"
    solara.lab.theme.themes.dark.primary = "#76591e"
    solara.lab.theme.dark = color._dark_theme

    v.Alert.element(
        children=["this is a test", f" - theme: {headers.value}"],
        color="primary",
    )

    gee_session = EESession(sepal_headers=headers.value)

    ee_number = ee.Number(1)

    value = get_info(gee_session, ee_number)

    solara.Markdown(
        f"""
        # {value}
    """
    )
