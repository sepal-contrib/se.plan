import requests
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

    v.Alert.element(
        children=["this is a test", f" - theme: {headers.value}"],
        color="primary",
    )

    base_url = "http://danielg.sepal.io/api/user-files/download"
    params = {"path": "/test.filelll"}

    response = requests.get(base_url, params=params, headers=headers.value)

    # Print out the response details
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)
