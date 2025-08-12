from sepal_ui.logger import setup_logging

logger = setup_logging(logger_name="SEPLAN")
logger.debug("Setting up SEPLAN application...")

import logging
from traitlets import Float, HasTraits, List, link

import solara
from solara.lab.components.theming import theme

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts.utils import init_ee
from sepal_ui.sepalwidgets.vue_app import ThemeToggle
from sepal_ui.solara import (
    setup_sessions,
    with_sepal_sessions,
    get_current_gee_interface,
    get_current_sepal_client,
    setup_theme_colors,
    setup_solara_server,
)

from component.frontend.icons import icon
from component.model.recipe import Recipe
from component.tile.custom_aoi_tile import AoiTile
from component.tile.dashboard_tile import DashboardTile
from component.tile.map_tile import MapTile
from component.tile.questionnaire_tile import QuestionnaireTile
from component.tile.recipe_tile import RecipeView
from component.model.app_model import AppModel
from component.message import cm
from component.widget.custom_widgets import (
    CustomApp,
    CustomAppBar,
    CustomDrawerItem,
    CustomNavDrawer,
    CustomTileAbout,
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sepalui").setLevel(logging.DEBUG)


init_ee()
setup_solara_server()


@solara.lab.on_kernel_start
def init_gee():
    return setup_sessions()


class MapLocation(HasTraits):
    zoom = Float(5).tag(sync=True)
    center = List([0, 0]).tag(sync=True)


@solara.component
@with_sepal_sessions(module_name="se.plan")
def Page():

    setup_theme_colors()
    theme_toggle = ThemeToggle()
    theme_toggle.observe(lambda e: setattr(theme, "dark", e["new"]), "dark")

    map_location = MapLocation()

    gee_interface = get_current_gee_interface()
    sepal_client = get_current_sepal_client()

    app_model = AppModel()
    recipe = Recipe(sepal_session=sepal_client, gee_interface=gee_interface)

    app_model.ready = True

    recipe_tile = RecipeView(
        recipe=recipe, app_model=app_model, sepal_session=sepal_client
    )
    aoi_tile = AoiTile(
        gee_interface=gee_interface, recipe=recipe, theme_toggle=theme_toggle
    )

    questionnaire_tile = QuestionnaireTile(
        gee_interface=gee_interface,
        recipe=recipe,
        theme_toggle=theme_toggle,
    )

    map_tile = MapTile(
        app_model=app_model,
        recipe=recipe,
        theme_toggle=theme_toggle,
        gee_interface=gee_interface,
        sepal_session=sepal_client,
    )

    link((aoi_tile.map_, "zoom"), (map_location, "zoom"))
    link((aoi_tile.map_, "center"), (map_location, "center"))

    link((map_tile.map_, "zoom"), (map_location, "zoom"))
    link((map_tile.map_, "center"), (map_location, "center"))

    dashboard_tile = DashboardTile(
        gee_interface=gee_interface,
        recipe=recipe,
        theme_toggle=theme_toggle,
        sepal_session=sepal_client,
    )

    disclaimer_tile = sw.TileDisclaimer(theme_toggle=theme_toggle)
    about_tile = CustomTileAbout(cm.app.about, theme_toggle=theme_toggle)
    about_tile.set_title("")

    app_bar = CustomAppBar(title=cm.app.title, theme_toggle=theme_toggle)
    app_content = [
        about_tile,
        aoi_tile,
        questionnaire_tile,
        map_tile,
        dashboard_tile,
        recipe_tile,
        disclaimer_tile,
    ]

    aux_drawers = {
        "about_tile": {
            "title": cm.app.drawer.about,
            "icon": icon("help-circle"),
        },
        "recipe_tile": {
            "title": cm.app.drawer.recipe,
            "icon": icon("question-file"),
        },
    }

    app_drawers = {
        "aoi_tile": {
            "title": cm.app.drawer.aoi,
            "icon": icon("location"),
        },
        "questionnaire_tile": {
            "title": cm.app.drawer.question,
            "icon": icon("help-circle"),
        },
        "map_tile": {
            "title": cm.app.drawer.map,
            "icon": icon("map"),
        },
        "dashboard_tile": {
            "title": cm.app.drawer.dashboard,
            "icon": icon("dashboard"),
        },
    }
    aux_items = [
        CustomDrawerItem(**aux_drawers[key], card=key) for key in aux_drawers.keys()
    ]

    app_items = [
        CustomDrawerItem(
            **app_drawers[key], card=key, model=app_model, bind_var="ready"
        )
        for key in app_drawers.keys()
    ]

    items = aux_items + app_items

    code_link = "https://github.com/sepal-contrib/se.plan"
    wiki_link = "https://docs.sepal.io/en/latest/modules/dwn/seplan.html"
    issue_link = "https://github.com/sepal-contrib/se.plan/issues/new"

    app_drawer = CustomNavDrawer(
        items, code=code_link, wiki=wiki_link, issue=issue_link, app_model=app_model
    )
    # build the Html final app by gathering everything
    CustomApp.element(
        app_model=app_model,
        tiles=app_content,
        appBar=app_bar,
        navDrawer=app_drawer,
        theme_toggle=theme_toggle,
    )
