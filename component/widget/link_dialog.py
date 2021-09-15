import ipyvuetify as v

from sepal_ui import sepalwidgets as sw

from component.message import cm


class LinkDialog(sw.SepalWidget, v.Dialog):
    def __init__(self):

        title = v.CardTitle(children=[cm.quintile.clip.title])
        self.link = v.TextField(
            class_="ma-5",
            v_model=None,
            outlined=True,
            label=cm.quintile.clip.lbl,
            hint=cm.quintile.clip.hint,
            persistent_hint=True,
            readonly=True,
            append_icon="mdi-clipboard-outline",
        )

        self.done = v.Btn(
            color="primary", outlined=True, children=[cm.quintile.clip.done]
        )

        self.card = v.Card(
            children=[title, self.link, v.CardActions(children=[self.done])]
        )

        super().__init__(
            value=False, persistent=True, max_width="600px", children=[self.card]
        )

        # js links
        self.done.on_event("click", self._done_click)

    def fire_dialog(self, link):
        """fire the dialog with a new link"""

        self.value = True
        self.link.v_model = link

        return self

    def _done_click(self, widget, data, event):

        # close without doing anything
        self.value = False

        return
