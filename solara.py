print("importing")
import sepal_ui.sepalwidgets as sw

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


@solara.component
def Page():

    app_model = AppModel()
    alert = AlertState()
    recipe = Recipe()
    recipe.load_model()

    solara_basemap_tiles = {k: eval(str(v)) for k, v in basemap_tiles.items()}

    # RecipeView.element(recipe=recipe, app_model=app_model, alert=alert)
    # AoiTile.element(
    #     recipe=recipe, build_alert=alert, solara_basemap_tiles=solara_basemap_tiles
    # )

    # QuestionnaireTile.element(
    #     recipe=recipe, build_alert=alert, solara_basemap_tiles=solara_basemap_tiles
    # )

    # MapTile(
    #     app_model=app_model,
    #     recipe=recipe,
    #     build_alert=alert,
    #     solara_basemap_tiles=solara_basemap_tiles,
    # )

    # DashboardTile.element(recipe=recipe, build_alert=alert)

    app_model.ready = True

    recipe_tile = RecipeView(recipe=recipe, app_model=app_model, alert=alert)
    aoi_tile = AoiTile(
        recipe=recipe, build_alert=alert, solara_basemap_tiles=solara_basemap_tiles
    )

    questionnaire_tile = QuestionnaireTile(
        recipe=recipe, build_alert=alert, solara_basemap_tiles=solara_basemap_tiles
    )

    map_tile = MapTile(
        app_model=app_model,
        recipe=recipe,
        build_alert=alert,
        solara_basemap_tiles=solara_basemap_tiles,
    )

    dashboard_tile = DashboardTile(recipe=recipe, build_alert=alert)

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
