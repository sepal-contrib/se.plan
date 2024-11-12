print("importing")
import sepal_ui.sepalwidgets as sw
from eeclient.client import EESession
from solara.lab import headers


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
import solara
from component.tile.recipe_tile import RecipeView
from component.model.app_model import AppModel

from sepal_ui.mapping.basemaps import basemap_tiles
from component.message import cm

from ipyleaflet import TileLayer

import solara.server.settings
import solara.settings

solara.server.settings.assets.fontawesome_path = "/font-awesome/6.2.1/css/all.min.css"
solara.server.settings.assets.extra_locations = ["./assets/"]
solara.settings.assets.cdn = "https://cdnjs.cloudflare.com/ajax/libs/"
solara.server.settings.main.root_path = "/api/app-launcher/seplan/"


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
# solara.lab.theme.themes.light.success = v.theme.themes.light.success
# solara.lab.theme.themes.light.info = v.theme.themes.light.info
# solara.lab.theme.themes.light.warning = v.theme.themes.light.warning
# solara.lab.theme.themes.light.error = v.theme.themes.light.error
solara.lab.theme.themes.light.main = "#2196f3"
solara.lab.theme.themes.light.darker = "#ffffff"
solara.lab.theme.themes.light.bg = "#FFFFFF"
solara.lab.theme.themes.light.menu = "#FFFFFF"


@solara.component
def Page():

    access_token = str(headers.value["access_token"][0])
    access_token_expiry_date = int(headers.value["access_token_expiry_date"][0])
    project_id = str(headers.value["project_id"][0])

    sepal_headers = {
        "id": 1,
        "username": "dguerrero",
        "googleTokens": {
            "accessToken": access_token,
            "accessTokenExpiryDate": access_token_expiry_date,
            "projectId": project_id,
            "refreshToken": "",
            "REFRESH_IF_EXPIRES_IN_MINUTES": 10,
            "legacyProject": "",
        },
        "status": "ACTIVE",
        "roles": ["USER"],
        "systemUser": False,
        "admin": False,
    }
    print(sepal_headers)
    user_session = EESession(sepal_headers, force_refresh=True)

    app_model = AppModel()
    alert = AlertState()
    recipe = Recipe()

    solara_basemap_tiles = {k: eval(str(v)) for k, v in basemap_tiles.items()}

    app_model.ready = True

    recipe_tile = RecipeView(recipe=recipe, app_model=app_model)
    aoi_tile = AoiTile(
        ee_session=user_session,
        recipe=recipe,
        solara_basemap_tiles=solara_basemap_tiles,
    )

    questionnaire_tile = QuestionnaireTile(
        ee_session=user_session,
        recipe=recipe,
        solara_basemap_tiles=solara_basemap_tiles,
    )

    map_tile = MapTile(
        app_model=app_model,
        recipe=recipe,
        solara_basemap_tiles=solara_basemap_tiles,
    )

    dashboard_tile = DashboardTile(recipe=recipe)

    disclaimer_tile = sw.TileDisclaimer()
    about_tile = CustomTileAbout(cm.app.about)
    about_tile.set_title("")

    app_bar = CustomAppBar(cm.app.title)
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
            "icon": "mdi-help-circle",
        },
        "recipe_tile": {
            "title": cm.app.drawer.recipe,
            "icon": "mdi-note-text",
        },
    }

    app_drawers = {
        "aoi_tile": {
            "title": cm.app.drawer.aoi,
            "icon": "mdi-map-marker-check",
        },
        "questionnaire_tile": {
            "title": cm.app.drawer.question,
            "icon": "mdi-file-question",
        },
        "map_tile": {
            "title": cm.app.drawer.map,
            "icon": "mdi-map",
        },
        "dashboard_tile": {
            "title": cm.app.drawer.dashboard,
            "icon": "mdi-view-dashboard",
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
        app_model=app_model, tiles=app_content, appBar=app_bar, navDrawer=app_drawer
    )
