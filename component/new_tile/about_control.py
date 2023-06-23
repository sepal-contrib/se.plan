from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from sepal_ui.message import ms

from component.message import cm


class Btn(sw.Btn):
    """Helper class to create about btns"""

    def __init__(self, name: str, faicon: str, href: str) -> None:

        super().__init__(name, f"fa-solid fa-{faicon}", href=href, target="_blank")


class AboutControl(sm.MenuControl):
    def __init__(self, **kwargs):

        # create an about tile
        tile = sw.TileAbout(cm.app.about)

        # customize the action section to add the github links
        code_btn = Btn(
            ms.widgets.navdrawer.code,
            "file-code",
            "https://github.com/sepal-contrib/se.plan",
        )
        issue_btn = Btn(
            ms.widgets.navdrawer.bug,
            "bug",
            "https://github.com/sepal-contrib/se.plan/issues/new",
        )
        doc_btn = Btn(
            ms.widgets.navdrawer.wiki,
            "book-open",
            "https://docs.sepal.io/en/latest/modules/dwn/seplan.html",
        )
        actions = sw.CardActions(
            children=[sw.Divider(), code_btn, issue_btn, doc_btn, sw.Divider()]
        )
        tile.children += [actions]

        super().__init__(
            icon_content="fa-solid fa-question",
            card_content=tile,
            fullscreen=True,
            fullapp=True,
            **kwargs,
        )
