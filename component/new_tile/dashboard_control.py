"""the dashboard interaction panel"""

from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from sepal_ui.message import ms

from component.message import cm


class DashBoardControl(sm.MenuControl):
    def __init__(self, **kwargs):

        # create the empt dashboard tile
        self.tile = sw.Tile("nested", "")

        # add a single button to create the dashboard
        btn = sw.Btn("Compute dashboard", "fa-solid fa-cogs")

        self.actions = sw.CardActions(children=[sw.Divider(), btn, sw.Divider()])
        self.tile.children += [self.actions]

        super().__init__(
            icon_content="fa-solid fa-cogs",
            card_content=self.tile,
            fullscreen=True,
            fullapp=True,
            **kwargs,
        )

        # add js behaviour
        btn.on_event("click", self.compute_dashboard)

    def compute_dashboard(self) -> None:

        extra = sw.Layout(children=["toto"])
        self.tile.children = [self.actions, extra]
