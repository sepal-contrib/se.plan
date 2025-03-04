from pathlib import Path
from typing import List, Literal, Union
from eeclient.client import EESession

import ee
from sepal_ui import mapping as sm

from component.message import cm
from component.scripts.logger import logger
from component.scripts.assets import default_asset_id


def get_layer(
    gee_session: EESession,
    image: ee.Image,
    vis_params: dict = {},
    name: str = "",
    visible: bool = True,
) -> sm.layer.EELayer:

    map_id_dict = gee_session.operations.get_map_id(image, vis_params)

    return sm.layer.EELayer(
        ee_object=image,
        url=map_id_dict["tile_fetcher"].url_format,
        attribution="Google Earth Engine",
        name=name,
        opacity=1,
        visible=visible,
        max_zoom=24,
    )


def get_limits(
    gee_session: EESession,
    asset: str,
    data_type: Literal["binary", "continuous", "categorical"],
    aoi: Union[ee.FeatureCollection, ee.Geometry],
    factor: int = 2,
) -> List[int]:
    """Computes limits or histogram keys for the given Earth Engine image based on the specified data type.

    Args:
        asset (str): Google Earth Engine asset ID.
        data_type (str): Either 'binary', 'continuous', or any other type indicating the type of data processing.
        aoi (ee.Geometry): Area of interest.
        band_index (int, optional): Band index to select from the image. Defaults to 0.
        factor (int, optional): Factor to multiply the nominal scale of the image. Defaults to 2 (i.e. 2x the nominal scale

    Returns:
        list: A list containing either min-max values or histogram keys depending on the data_type.
    """

    # We know that the treecover_with_potential asset is binary
    if asset == default_asset_id:
        return [0, 1]

    if data_type in ["binary", "continuous"]:
        reducer = ee.Reducer.minMax()

        def get_value(reduction):
            return list(gee_session.operations.get_info(reduction).values())

    else:
        reducer = ee.Reducer.frequencyHistogram()

        def get_value(reduction):
            return gee_session.operations.get_info(
                ee.Dictionary(reduction.get(ee.Image(asset).bandNames().get(0))).keys(),
            )

    ee_image = ee.Image(asset).select(0)
    # Multiply the nominal scale by 2 in case the nominal scale is finer than 45
    scale = ee.Number(
        ee.Algorithms.If(
            ee_image.projection().nominalScale().lt(30),
            ee_image.projection().nominalScale().multiply(2),
            ee_image.projection().nominalScale(),
        )
    )

    # If scale is less than 30, set it to 30
    scale = ee.Algorithms.If(scale.lt(30), 30, scale)

    values = get_value(
        ee_image.reduceRegion(
            reducer=reducer,
            geometry=aoi,
            scale=scale,
            maxPixels=1e13,
        )
    )

    logger.debug("get_limits_values:", values)

    # check if values are none and if so, raise a ValueError
    if any([val is None for val in values]):
        raise ValueError(cm.questionnaire.error.no_limits)

    # depending on the scale, values from the histogram can be floats, we'll
    # convert them to integers... sometimes we'll show more values than the
    # asset really has
    return sorted(set(int(float(val)) for val in values))


def get_gee_recipe_folder(recipe_name: str, gee_session: EESession) -> Path:
    """Create a folder for the recipe in GEE"""

    try:
        if gee_session:
            recipe_folder = Path("seplan") / recipe_name
            return Path(gee_session.operations.create_folder(recipe_folder))

        else:
            project_folder = Path(f"projects/{ee.data._cloud_api_user_project}/assets/")
            seplan_folder = project_folder / "seplan"
            recipe_folder = seplan_folder / recipe_name

            if not ee.data.getInfo(str(seplan_folder)):
                ee.data.createAsset({"type": "FOLDER"}, str(seplan_folder))

            # Create the recipe folder
            if not ee.data.getInfo(str(recipe_folder)):
                ee.data.createAsset({"type": "FOLDER"}, str(recipe_folder))

            return Path(recipe_folder)

    except Exception as e:

        logger.debug("Error in get_gee_recipe_folder:", e)
        raise Exception("Eror in folder recipe folder creation")
