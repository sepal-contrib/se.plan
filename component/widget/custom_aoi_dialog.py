from sepal_ui import sepalwidgets as sw
import ipyvuetify as v

from component.message import cm


class CustomAoiDialog(sw.Dialog):

    feature = None
    "the geo_json feature selected by th user"

    def __init__(self):

        # create the widgets
        self.w_name = sw.TextField(label=cm.map.dialog.label, v_model=None)
        self.btn = sw.Btn(cm.map.dialog.btn, "mdi-check")
        title = sw.CardTitle(children=[cm.map.dialog.title])
        text = sw.CardText(children=[self.w_name])
        action = sw.CardActions(children=[self.btn])
        card = sw.Card(class_="ma-5", children=[title, text, action])

        # init the dialog
        super().__init__(
            persistent=True, value=False, max_width="700px", children=[card]
        )

        # add js behavior
        self.btn.on_event("click", self._on_click)

    def _on_click(self, widget, data, event):

        # close the dialog
        # it will trigger the saving
        self.value = False

        return self

    def update_aoi(self, geo_json, index):
        """read the aoi and give an default name"""

        # update
        self.feature = geo_json
        self.w_name.v_model = f"sub AOI {index}"

        # show
        self.value = True

        return self
