from sepal_ui.logger import setup_logging

logger = setup_logging(logger_name="SEPLAN")
logger.debug("Setting up SEPLAN application...")

import logging
from pathlib import Path
from traitlets import Float, HasTraits, List, link

import solara
from solara.lab.components.theming import theme

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts.utils import init_ee
from sepal_ui.sepalwidgets.vue_app import MapApp, ThemeToggle
from sepal_ui.solara.components.admin import AdminButton

from sepal_ui.solara import (
    setup_sessions,
    with_sepal_sessions,
    get_current_gee_interface,
    get_current_sepal_client,
    setup_theme_colors,
    setup_solara_server,
    get_current_session_info,
)

from component.frontend.icons import icon
from component.model.recipe import Recipe
from component.tile.custom_aoi_tile import AoiView
from component.widget.map import SeplanMap
from component.tile.questionnaire_tile import QuestionnaireTile
from component.tile.recipe_tile import RecipeView
from component.tile.right_panel import get_right_panel_content
from component.model.app_model import AppModel
from component.message import cm
from component.widget.custom_widgets import CustomAppBar, CustomTileAbout

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sepalui").setLevel(logging.DEBUG)


init_ee()
setup_solara_server(extra_asset_locations=[str(Path(__file__).parent / "assets")])


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
    username = get_current_session_info()["username"]

    app_model = AppModel()
    recipe = Recipe(sepal_session=sepal_client, gee_interface=gee_interface)
    solara_admin = AdminButton(username)

    map_ = SeplanMap(
        recipe.seplan_aoi,
        theme_toggle=theme_toggle,
        gee_interface=gee_interface,
    )

    app_model.ready = True

    recipe_tile = RecipeView(
        recipe=recipe, app_model=app_model, sepal_session=sepal_client
    )
    aoi_view = AoiView(map_, gee_interface=gee_interface, recipe=recipe)

    questionnaire_tile = QuestionnaireTile(
        gee_interface=gee_interface,
        recipe=recipe,
        theme_toggle=theme_toggle,
    )

    link((aoi_view.map_, "zoom"), (map_location, "zoom"))
    link((aoi_view.map_, "center"), (map_location, "center"))

    disclaimer_tile = sw.TileDisclaimer(theme_toggle=theme_toggle)
    about_tile = CustomTileAbout(cm.app.about, theme_toggle=theme_toggle)

    app_bar = CustomAppBar(title=cm.app.title, theme_toggle=theme_toggle)

    steps_data = [
        {
            "id": 1,
            "name": cm.app.drawer.about,
            "icon": icon("help-circle"),
            "display": "dialog",
            "content": about_tile,
            "width": 1300,
        },
        {
            "id": 2,
            "name": cm.app.drawer.recipe,
            "icon": icon("question-file"),
            "display": "dialog",
            "content": recipe_tile,
        },
        {
            "id": 3,
            "name": cm.app.drawer.aoi,
            "icon": icon("location"),
            "display": "dialog",
            "content": aoi_view,
        },
        {
            "id": 4,
            "name": cm.app.drawer.question,
            "icon": icon("help-circle"),
            "display": "dialog",
            "content": questionnaire_tile,
            "width": 1300,
        },
        {
            "id": 6,
            "name": cm.app.drawer.dashboard,
            "icon": icon("dashboard"),
            "display": "step",
            "content": [],
            "right_panel_action": "toggle",  # "open", "close", "toggle", or None
        },
        {
            "id": 7,
            "name": "Disclaimer",
            "icon": icon("information"),
            "display": "dialog",
            "content": disclaimer_tile,
        },
    ]

    # Create the right panel with all dashboard components
    right_panel = get_right_panel_content(
        gee_interface=gee_interface,
        recipe=recipe,
        sepal_session=sepal_client,
        map_=map_,
        theme_toggle=theme_toggle,
    )
    # aux_drawers = {
    #     "about_tile": {
    #         "title": cm.app.drawer.about,
    #         "icon": icon("help-circle"),
    #     },
    #     "recipe_tile": {
    #         "title": cm.app.drawer.recipe,
    #         "icon": icon("question-file"),
    #     },
    # }

    # app_drawers = {
    #     "aoi_tile": {
    #         "title": cm.app.drawer.aoi,
    #         "icon": icon("location"),
    #     },
    #     "questionnaire_tile": {
    #         "title": cm.app.drawer.question,
    #         "icon": icon("help-circle"),
    #     },
    #     "map_tile": {
    #         "title": cm.app.drawer.map,
    #         "icon": icon("map"),
    #     },
    #     "dashboard_tile": {
    #         "title": cm.app.drawer.dashboard,
    #         "icon": icon("dashboard"),
    #     },
    # }
    # aux_items = [
    #     CustomDrawerItem(**aux_drawers[key], card=key) for key in aux_drawers.keys()
    # ]

    # app_items = [
    #     CustomDrawerItem(
    #         **app_drawers[key], card=key, model=app_model, bind_var="ready"
    #     )
    #     for key in app_drawers.keys()
    # ]

    # items = aux_items + app_items

    # app_drawer = CustomNavDrawer(
    #     items, code=code_link, wiki=wiki_link, issue=issue_link, app_model=app_model
    # )
    # build the Html final app by gathering everything
    # CustomApp.element(
    #     app_model=app_model,
    #     tiles=app_content,
    #     appBar=app_bar,
    #     navDrawer=app_drawer,
    #     theme_toggle=theme_toggle,
    # )

    MapApp.element(
        app_title="SEPLAN",
        app_icon="mdi-image-filter-hdr",
        main_map=[map_],
        steps_data=steps_data,
        initial_step=1,
        theme_toggle=[theme_toggle],
        dialog_width=860,
        right_panel=[right_panel],
        repo_url="https://github.com/sepal-contrib/se.plan",
        docs_url="https://docs.sepal.io/en/latest/modules/dwn/seplan.html",
    )
