from component.scripts.logger import setup_logging

setup_logging()
import os
from eeclient.client import EESession
from eeclient.helpers import get_sepal_headers_from_auth

from eeclient.exceptions import EEClientError
from eeclient.models import SepalHeaders

from traitlets import Float, HasTraits, List, link
import solara
import solara.server.settings
from solara.lab import headers
from solara.lab.components.theming import theme

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts.utils import init_ee
from sepal_ui.scripts.sepal_client import SepalClient
from sepal_ui.scripts.gee_interface import GEEInterface
from sepal_ui.sepalwidgets.vue_app import ThemeToggle

from component.frontend.icons import icon
from component.model.recipe import Recipe
from component.tile.custom_aoi_tile import AoiTile
from component.tile.dashboard_tile import DashboardTile
from component.tile.map_tile import MapTile
from component.tile.questionnaire_tile import QuestionnaireTile
from component.widget.custom_widgets import (
    CustomApp,
    CustomAppBar,
    CustomDrawerItem,
    CustomNavDrawer,
    CustomTileAbout,
)
from component.tile.recipe_tile import RecipeView
from component.model.app_model import AppModel
from component.message import cm

import logging

logger = logging.getLogger("SEPLAN")
import logging

logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)
logging.getLogger("eeclient").setLevel(logging.DEBUG)

init_ee()

sessions = {}


@solara.lab.on_kernel_start
def setup_gee_interface():
    session_id = solara.get_session_id()
    logger.debug(f"Session ID: {session_id}")

    # Wait for headers to be available, then create session
    def create_session():
        try:
            current_headers = headers.value
            if current_headers is None:
                logger.warning(f"Headers not available yet for session {session_id}")
                return None

            logger.debug(f"Headers available: {current_headers}")

            sepal_headers = (
                get_sepal_headers_from_auth()
                if os.getenv("SEPLAN_TEST", "false").lower() == "true"
                else SepalHeaders.model_validate(current_headers)
            )
            logger.debug(f"SEPAL-HEADERS: {sepal_headers}")

            sepal_session_id = sepal_headers.cookies["SEPAL-SESSIONID"]
            logger.debug(f"SEPAL-SESSIONID: {sepal_session_id}")

            gee_session = EESession(sepal_headers=sepal_headers)
            sessions[session_id] = (
                GEEInterface(gee_session),
                sepal_session_id,
            )
            logger.debug(f"Session {session_id} created successfully")
            return sessions[session_id]

        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
            if isinstance(e, EEClientError):
                logger.error("Authentication required: Please authenticate via sepal.")
            raise e

    # Try to create session immediately
    try:
        result = create_session()
        if result is None:
            logger.debug(
                f"Session {session_id} will be created when headers become available"
            )
    except Exception as e:
        logger.error(f"Failed to create session {session_id}: {e}")

    # Return cleanup function
    def cleanup():
        logger.debug(f"Cleaning up session {session_id}")
        if session_id in sessions:
            gee_interface, _ = sessions[session_id]
            try:
                gee_interface.close()
            except Exception as e:
                logger.error(f"Error closing GEE interface: {e}")
            del sessions[session_id]
            logger.debug(f"Session {session_id} cleaned up")

    return cleanup


solara.server.settings.assets.fontawesome_path = (
    "/@fortawesome/fontawesome-free@6.7.2/css/all.min.css"
)
solara.server.settings.assets.extra_locations = ["./assets/"]


class MapLocation(HasTraits):
    zoom = Float(5).tag(sync=True)
    center = List([0, 0]).tag(sync=True)


@solara.component
def Page():

    solara.lab.theme.themes.dark.primary = "#76591e"
    solara.lab.theme.themes.dark.primary_contrast = "#bf8f2d"
    solara.lab.theme.themes.dark.secondary = "#363e4f"
    solara.lab.theme.themes.dark.secondary_contrast = "#5d76ab"
    solara.lab.theme.themes.dark.error = "#a63228"
    solara.lab.theme.themes.dark.info = "#c5c6c9"
    solara.lab.theme.themes.dark.success = "#3f802a"
    solara.lab.theme.themes.dark.warning = "#b8721d"
    solara.lab.theme.themes.dark.accent = "#272727"
    solara.lab.theme.themes.dark.anchor = "#f3f3f3"
    solara.lab.theme.themes.dark.main = "#24221f"
    solara.lab.theme.themes.dark.darker = "#1a1a1a"
    solara.lab.theme.themes.dark.bg = "#121212"
    solara.lab.theme.themes.dark.menu = "#424242"
    solara.lab.theme.themes.light.primary = "#5BB624"
    solara.lab.theme.themes.light.primary_contrast = "#76b353"
    solara.lab.theme.themes.light.accent = "#f3f3f3"
    solara.lab.theme.themes.light.anchor = "#f3f3f3"
    solara.lab.theme.themes.light.secondary = "#2199C4"
    solara.lab.theme.themes.light.secondary_contrast = "#5d76ab"
    solara.lab.theme.themes.light.main = "#2196f3"
    solara.lab.theme.themes.light.darker = "#ffffff"
    solara.lab.theme.themes.light.bg = "#FFFFFF"
    solara.lab.theme.themes.light.menu = "#FFFFFF"

    theme_toggle = ThemeToggle()
    theme_toggle.observe(lambda e: setattr(theme, "dark", e["new"]), "dark")

    map_location = MapLocation()

    session_id = solara.get_session_id()

    logger.debug(f"sessions {sessions}")

    # Watch for headers and create session if not exists
    current_headers = headers.value
    if current_headers and session_id not in sessions:
        try:
            sepal_headers = (
                get_sepal_headers_from_auth()
                if os.getenv("SEPLAN_TEST", "false").lower() == "true"
                else SepalHeaders.model_validate(current_headers)
            )
            sepal_session_id = sepal_headers.cookies["SEPAL-SESSIONID"]
            gee_session = EESession(sepal_headers=sepal_headers)
            sessions[session_id] = (
                GEEInterface(gee_session),
                sepal_session_id,
            )
            logger.debug(f"Session {session_id} created in Page component")
        except Exception as e:
            logger.error(f"Error creating session in Page component: {e}")
            if isinstance(e, EEClientError):
                solara.Error(
                    f"Authentication required: Please authenticate via sepal. See https://docs.sepal.io/en/latest/setup/gee.html. for more information."
                )
                return
            solara.Error(f"An error has occurred: {e}")
            return

    gee_interface, sepal_session_id = sessions.get(session_id, (None, None))
    logger.debug(
        f"gee_interface: {gee_interface}, sepal_session_id: {sepal_session_id}"
    )

    # Show loading state if session is not ready
    if gee_interface is None or sepal_session_id is None:
        if current_headers is None:
            solara.Info("Waiting for authentication headers...")
        else:
            solara.Info("Initializing session...")
        return
    sepal_client = SepalClient(session_id=sepal_session_id, module_name="se.plan")

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
