from sepal_ui import mapping as sm
import ee


def get_layer(
    image: ee.Image, vis_params: dict, name: str, visible: bool
) -> sm.layer.EELayer:
    map_id_dict = ee.Image(image).getMapId(vis_params)

    return sm.layer.EELayer(
        ee_object=image,
        url=map_id_dict["tile_fetcher"].url_format,
        attribution="Google Earth Engine",
        name=name,
        opacity=1,
        visible=visible,
        max_zoom=24,
    )
