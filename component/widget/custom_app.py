from sepal_ui import sepalwidgets as sw
from sepal_ui import color
import ipyvuetify as v


class CustomApp(sw.App):
    def add_alert(self, msg, **kwargs):

        default_params = {
            "type": "info",
            "border": "left",
            "class_": "mt-5",
            "transition": "slide-x-transition",
            "prominent": True,
            "dismissible": True,
        }

        for p, val in default_params.items():
            if not p in kwargs:
                kwargs[p] = val

        # create the alert
        alert = v.Alert(children=[msg], **kwargs)

        # add the alert to the app
        self.content.children = [alert] + self.content.children.copy()

        return self
