import time

start = time.time()

import solara
import sepal_ui.sepalwidgets as sw
from component.model.recipe import Recipe
from component.tile.custom_aoi_tile import AoiTile
from component.widget.alert_state import AlertState
from component.model.app_model import AppModel
from sepal_ui.mapping.basemaps import basemap_tiles
from ipyleaflet import TileLayer

end_import = time.time()
print(f"Import time: {end_import - start}")


@solara.component
def Page():

    start = time.time()
    app_model = AppModel()
    alert = AlertState()
    recipe = Recipe()
    recipe.load_model()
    end = time.time()
    print(f"Model load time: {end - start}")

    solara_basemap_tiles = {k: eval(str(v)) for k, v in basemap_tiles.items()}

    start = time.time()
    AoiTile.element(
        recipe=recipe, build_alert=alert, solara_basemap_tiles=solara_basemap_tiles
    )
    end = time.time()
    print(f"AoiTile load time: {end - start}")
