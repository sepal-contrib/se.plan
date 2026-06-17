import logging
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

import ee
from ipyleaflet import TileLayer
from sepal_ui import mapping as sm
from sepal_ui.mapping.visualization import set_viz_params
from sepal_ui.scripts.gee import get_ee_project
from sepal_ui.scripts.gee_interface import GEEInterface

from component import parameter as cp
from component.message import cm
from component.scripts.assets import default_asset_id

logger = logging.getLogger("SEPLAN")


def get_ee_project_id(gee_interface: GEEInterface) -> str:
    """Return the Cloud project id backing the current Earth Engine session.

    Prefers the session-backed project id (the user's project that actually
    submits the export task), falling back to the default project reported by
    the Earth Engine API when no session is attached (e.g. local runs).

    Args:
        gee_interface: The interface used to run Earth Engine operations.

    Returns:
        The Cloud project id (e.g. ``ee-indonesia-gwl``).
    """
    session = getattr(gee_interface, "session", None)
    project_id = getattr(session, "project_id", None)

    return project_id or get_ee_project()


async def get_layer_min_max(
    image: ee.Image, aoi: ee.FeatureCollection, gee_interface: GEEInterface
) -> Tuple[float, float]:
    """Compute the (min, max) of an image over the AOI.

    Mirrors the reducer used by the layer preview map so the embedded
    visualization stretch matches what users saw on screen.

    Args:
        image: The single-band image to reduce.
        aoi: The area of interest to reduce over.
        gee_interface: The interface used to run the (awaited) reduction.

    Returns:
        A ``(min, max)`` tuple rounded to two decimals.
    """
    # Clip to the AOI + reduce over its bounding box. aoi.geometry() would
    # dissolve the whole collection (Collection.geometry) and blow EE's 2M-edge
    # limit for dense GAUL 2024 boundaries (e.g. Indonesia). Imported here to
    # avoid a module-level import cycle with seplan.
    from component.scripts.seplan import _aoi_bbox

    clipped = image.clip(aoi)
    reduced = clipped.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=_aoi_bbox(aoi),
        scale=1,
        maxPixels=int(1e5),
        bestEffort=True,
        tileScale=16,
    )
    values = await gee_interface.get_info_async(reduced)
    values = values or {}

    min_ = next((v for k, v in values.items() if k.endswith("_min")), None)
    max_ = next((v for k, v in values.items() if k.endswith("_max")), None)

    min_ = 0 if min_ is None else round(min_, 2)
    max_ = min_ + 1 if max_ is None else round(max_, 2)

    return min_, max_


def get_export_viz_params(
    theme: str,
    id_: str,
    min_max: Optional[Tuple[float, float]] = None,
    bands: Optional[List[str]] = None,
) -> dict:
    """Build ``set_viz_params`` kwargs that reproduce a layer's on-map styling.

    The returned SEPAL-convention parameters mirror the palettes the app uses
    on the map (``layer_vis`` for the suitability indices, ``map_vis`` for the
    individual themes) so an exported asset styles itself when reloaded.

    Args:
        theme: The export theme — ``index``, ``benefit``, ``constraint`` or
            ``cost``.
        id_: The layer id within the theme. Unused today; kept so per-layer
            palettes can be added without changing callers.
        min_max: Pre-computed ``(min, max)`` for the continuous themes
            (``benefit`` / ``cost``). Falls back to the palette defaults.
        bands: The band name(s) the visualization targets. Added as
            ``visualization_*_bands`` when provided so SEPAL readers know
            which band to render.

    Returns:
        A kwargs dict for :func:`set_viz_params`, or ``{}`` when the theme has
        no defined palette.
    """
    if theme == "index":
        params = {
            "name": "default",
            "type": "continuous",
            "min": cp.layer_vis["min"],
            "max": cp.layer_vis["max"],
            "palette": cp.layer_vis["palette"],
        }
    elif theme == "constraint":
        binary = cp.map_vis["binary"]
        params = {
            "name": "default",
            "type": "categorical",
            "values": [0, 1],
            "labels": binary["names"],
            "min": binary["min"],
            "max": binary["max"],
            "palette": binary["palette"],
        }
    elif theme in ("benefit", "cost"):
        gradient = cp.map_vis["gradient"]
        min_, max_ = min_max or (gradient["min"], gradient["max"])
        params = {
            "name": "default",
            "type": "continuous",
            "min": min_,
            "max": max_,
            "palette": gradient["palette"],
        }
    else:
        return {}

    if bands:
        params["bands"] = bands

    return params


async def apply_export_viz(
    image: ee.Image,
    theme: str,
    id_: str,
    aoi: ee.FeatureCollection,
    gee_interface: GEEInterface,
) -> ee.Image:
    """Annotate ``image`` with the map's visualization as SEPAL properties.

    Continuous themes (``benefit`` / ``cost``) get a data-driven stretch; the
    suitability ``index`` and ``constraint`` themes use their fixed palettes.
    Returns the image unchanged for themes without a defined palette, and never
    raises — a failed stretch falls back to the palette defaults.

    All Earth Engine reads use the awaited async interface, so this must be
    called from an async context (e.g. a ``gee_interface.create_task`` body).

    Args:
        image: The image about to be exported to an Earth Engine asset.
        theme: The export theme.
        id_: The layer id within the theme.
        aoi: The area of interest, used to compute the stretch.
        gee_interface: The interface used to run the awaited Earth Engine reads.

    Returns:
        The image carrying ``visualization_*`` properties, or the original
        image when the theme has no palette.
    """
    # cheap purity check first so an unknown theme makes no Earth Engine calls
    if not get_export_viz_params(theme, id_):
        return image

    min_max = None
    if theme in ("benefit", "cost"):
        try:
            min_max = await get_layer_min_max(image, aoi, gee_interface)
        except Exception:
            logger.debug("min/max computation failed; using palette defaults")

    # resolve the real band name so the asset carries visualization_*_bands
    bands = None
    try:
        band_names = await gee_interface.get_info_async(image.bandNames())
        bands = band_names[:1] if band_names else None
    except Exception:
        logger.debug("band name resolution failed; exporting without bands")

    viz_params = get_export_viz_params(theme, id_, min_max, bands)

    return set_viz_params(image, **viz_params)


def create_layer(map_id_dict: dict, name: str = "", visible: bool = True) -> TileLayer:
    return TileLayer(
        url=map_id_dict["tile_fetcher"].url_format,
        attribution="Google Earth Engine",
        name=name,
        max_zoom=24,
    )


def get_layer(
    gee_interface: GEEInterface,
    image: ee.Image,
    vis_params: dict = {},
    name: str = "",
    visible: bool = True,
) -> sm.layer.EELayer:

    map_id_dict = gee_interface.get_map_id(image, vis_params)

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
    gee_interface: GEEInterface,
    asset: str,
    data_type: Literal["binary", "continuous", "categorical"],
    aoi: Union[ee.FeatureCollection, ee.Geometry],
    factor: int = 2,
) -> List[int]:
    """Computes limits or histogram keys for the given Earth Engine image based on the specified data type.

    Args:
        gee_interface (GEEInterface): The interface used to run Earth Engine operations.
        asset (str): Google Earth Engine asset ID.
        data_type (str): Either 'binary', 'continuous', or any other type indicating the type of data processing.
        aoi (ee.Geometry): Area of interest.
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
            return list(gee_interface.get_info(reduction).values())

    else:
        reducer = ee.Reducer.frequencyHistogram()

        def get_value(reduction):
            return gee_interface.get_info(
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

    logger.debug(f"get_limits_values: {values}")

    # check if values are none and if so, raise a ValueError
    if any([val is None for val in values]):
        raise ValueError(cm.questionnaire.error.no_limits)

    # depending on the scale, values from the histogram can be floats, we'll
    # convert them to integers... sometimes we'll show more values than the
    # asset really has
    return sorted(set(int(float(val)) for val in values))


async def get_limits_async(
    gee_interface: GEEInterface,
    asset: str,
    data_type: Literal["binary", "continuous", "categorical"],
    aoi: Union[ee.FeatureCollection, ee.Geometry],
    factor: int = 2,
) -> List[int]:
    """Async version of get_limits function.

    Computes limits or histogram keys for the given Earth Engine image based on the specified data type.

    Args:
        gee_interface (GEEInterface): The GEE interface for async operations.
        asset (str): Google Earth Engine asset ID.
        data_type (str): Either 'binary', 'continuous', or any other type indicating the type of data processing.
        aoi (ee.Geometry): Area of interest.
        factor (int, optional): Factor to multiply the nominal scale of the image. Defaults to 2.

    Returns:
        list: A list containing either min-max values or histogram keys depending on the data_type.
    """
    # We know that the treecover_with_potential asset is binary
    if asset == default_asset_id:
        return [0, 1]

    if data_type in ["binary", "continuous"]:
        reducer = ee.Reducer.minMax()

        async def get_value_async(reduction):
            result = await gee_interface.get_info_async(reduction)
            return list(result.values())

    else:
        reducer = ee.Reducer.frequencyHistogram()

        async def get_value_async(reduction):
            keys = await gee_interface.get_info_async(
                ee.Dictionary(reduction.get(ee.Image(asset).bandNames().get(0))).keys()
            )
            return keys

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

    # Clip to the AOI + reduce over its bbox; geometry=aoi would dissolve the
    # whole collection (Collection.geometry) and blow EE's 2M-edge limit for
    # dense GAUL 2024 boundaries (e.g. Indonesia). Imported here to avoid a
    # module-level import cycle with seplan.
    from component.scripts.seplan import _aoi_bbox

    reduction = ee_image.clip(aoi).reduceRegion(
        reducer=reducer,
        geometry=_aoi_bbox(aoi),
        scale=scale,
        maxPixels=1e13,
    )

    values = await get_value_async(reduction)

    logger.debug(f"get_limits_async_values: {values}")

    # check if values are none and if so, raise a ValueError
    if any([val is None for val in values]):
        raise ValueError(cm.questionnaire.error.no_limits)

    # depending on the scale, values from the histogram can be floats, we'll
    # convert them to integers... sometimes we'll show more values than the
    # asset really has
    return sorted(set(int(float(val)) for val in values))


def get_gee_recipe_folder(recipe_name: str, gee_interface: GEEInterface) -> Path:
    """Create a folder for the recipe in GEE."""
    recipe_folder = Path("seplan") / recipe_name
    return Path(gee_interface.create_folder(recipe_folder.as_posix()))


async def get_gee_recipe_folder_async(
    recipe_name: str, gee_interface: GEEInterface
) -> Path:
    """Create (awaited) the recipe's GEE folder and return its path.

    Async mirror of :func:`get_gee_recipe_folder` for use inside
    ``gee_interface.create_task`` bodies, where blocking calls would deadlock.

    Args:
        recipe_name: The recipe stem used as the folder name.
        gee_interface: The interface used to create the folder.

    Returns:
        The created folder as a :class:`~pathlib.Path`.
    """
    recipe_folder = Path("seplan") / recipe_name
    created = await gee_interface.create_folder_async(recipe_folder.as_posix())

    # create_folder_async may return the asset path (str) or an asset dict
    if isinstance(created, dict):
        created = created.get("name") or created.get("id") or created.get("path")

    return Path(created)
