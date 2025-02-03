import ipyvuetify as v
from component.frontend.icons import icon
import sepal_ui.sepalwidgets as sw

btn_color = "primary"


class IconBtn(sw.Btn):
    def __init__(self, gliph: str, *args, **kwargs):

        kwargs["icon"] = kwargs.get("icon", True)
        kwargs["small"] = kwargs.get("small", True)
        kwargs["class_"] = kwargs.get("class_", "mr-2")

        super().__init__(gliph=gliph, *args, **kwargs)

        # to overwrite the default color
        self.color = kwargs.get("color") or btn_color
        self.v_icon.left = False


class TextBtn(sw.Btn):
    def __init__(self, text: str, *args, **kwargs):

        kwargs["small"] = True
        kwargs["class_"] = "mr-2"

        super().__init__(msg=text, *args, **kwargs)

        # to overwrite the default color
        self.color = btn_color


class DrawMenuBtn(v.Btn):

    def __init__(self, *args, **kwargs):

        self.v_on = "menuData.on"
        self.small = True
        self.children = [
            v.Icon(children=[icon("draw")], small=True, color="white"),
            v.Icon(
                children=["fa fa-caret-down"],
                small=True,
                right=True,
                color="white",
            ),
        ]

        super().__init__(*args, **kwargs)
        self.class_ = "mr-2"
        self.color = btn_color


class CompareBtn(v.Flex):
    def __init__(self):

        # to align the flex container to the right
        self.style_ = "flex: 0"

        super().__init__()

        self.color = "primary"
        self.btn = IconBtn(icon("map"))
        self.children = [self.btn]
