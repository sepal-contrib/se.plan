from typing import Dict

from traitlets import Bool, Float, HasTraits, List, Unicode, link, observe
from component.frontend.icons import icon
import sepal_ui.sepalwidgets as sw
import solara
from eeclient.client import EESession
from solara.lab import headers
import solara.server.settings
import solara.settings
from solara.lab.components.theming import theme
from sepal_ui.frontend.resize_trigger import ResizeTrigger
from sepal_ui.scripts.utils import init_ee

from component.model.recipe import Recipe
from component.tile.custom_aoi_tile import AoiTile
from component.tile.dashboard_tile import DashboardTile
from component.tile.map_tile import MapTile
from component.tile.questionnaire_tile import QuestionnaireTile
from component.widget.alert_state import AlertState
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


import ee

init_ee()

# solara.server.settings.main.root_path = "/api/app-launcher/seplan"
solara.server.settings.assets.fontawesome_path = (
    "/@fortawesome/fontawesome-free@6.7.2/css/all.min.css"
)
solara.server.settings.assets.extra_locations = ["./assets/"]
session_storage: Dict[str, str] = {}

# used only to force updating of the page
force_update_counter = solara.reactive(0)


def store_in_session_storage(value):
    session_storage[solara.get_session_id()] = value
    force_update_counter.value += 1


class MapLocation(HasTraits):
    zoom = Float(5).tag(sync=True)
    center = List([0, 0]).tag(sync=True)


class SolaraTheme(HasTraits):
    dark = Bool(session_storage.get(solara.get_session_id(), True)).tag(sync=True)
    name = Unicode().tag(sync=True)

    def __init__(self):
        super().__init__()
        self.name = self.get_theme_name()

    @observe("dark")
    def on_change(self, change):
        theme.dark = self.dark
        self.name = self.get_theme_name()
        store_in_session_storage(self.dark)

    def get_theme_name(self):
        return "dark" if self.dark else "light"


@solara.component
def Page():

    solara_theme_obj = SolaraTheme()
    theme.dark = solara_theme_obj.dark
    map_location = MapLocation()
    ResizeTrigger.element()

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

    try:
        gee_session = EESession(sepal_headers=headers.value)
    except Exception as e:
        solara.Markdown(f"An error has occured: {e}")
        raise e

    app_model = AppModel()
    alert = AlertState()
    recipe = Recipe()

    app_model.ready = True

    recipe_tile = RecipeView(recipe=recipe, app_model=app_model)
    aoi_tile = AoiTile(
        gee_session=gee_session, recipe=recipe, solara_theme_obj=solara_theme_obj
    )

    questionnaire_tile = QuestionnaireTile(
        gee_session=gee_session,
        recipe=recipe,
        solara_theme_obj=solara_theme_obj,
    )

    map_tile = MapTile(
        app_model=app_model,
        recipe=recipe,
        solara_theme_obj=solara_theme_obj,
        gee_session=gee_session,
    )

    link((aoi_tile.map_, "zoom"), (map_location, "zoom"))
    link((aoi_tile.map_, "center"), (map_location, "center"))

    link((map_tile.map_, "zoom"), (map_location, "zoom"))
    link((map_tile.map_, "center"), (map_location, "center"))

    dashboard_tile = DashboardTile(gee_session=gee_session, recipe=recipe)

    disclaimer_tile = sw.TileDisclaimer(solara_theme_obj=solara_theme_obj)
    about_tile = CustomTileAbout(cm.app.about, solara_theme_obj=solara_theme_obj)
    about_tile.set_title("")

    app_bar = CustomAppBar(title=cm.app.title, solara_theme_obj=solara_theme_obj)
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
        solara_theme_obj=solara_theme_obj,
    )
