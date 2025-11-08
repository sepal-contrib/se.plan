from typing import Dict, List, Union
import logging
import asyncio
import ee
from sepal_ui.scripts.gee_interface import GEEInterface

from component.model.recipe import Recipe
from component.scripts.seplan import reduce_constraints
from component.types import (
    MeanStatsDict,
    MeanStatsValues,
    PercentageStatsDict,
    RecipeStatsDict,
    SumStatsDict,
)

logger = logging.getLogger("SEPLAN")


def is_main_aoi(main_aoi_name, aoi_name) -> bool:
    """Check if the aoi is the main aoi."""
    return main_aoi_name == aoi_name


async def get_summary_statistics_async(
    gee_interface: GEEInterface, recipe: Recipe
) -> RecipeStatsDict:
    """Returns summary statistics using seplan inputs with automatic fallback.

    The statistics will be later parsed to be displayed in the dashboard.

    This function first attempts sequential AOI processing. If it encounters a 429 error
    (Too many concurrent aggregations), it automatically falls back to a batched processing
    approach that processes statistics in smaller chunks.

    Args:
        gee_interface: The GEE interface for async operations
        recipe: The recipe to compute statistics for

    """
    try:
        return await _get_summary_statistics_sequential(gee_interface, recipe)
    except Exception as e:
        error_msg = str(e).lower()

        if (
            "429" in error_msg
            or "concurrent aggregation" in error_msg
            or "resource_exhausted" in error_msg
        ):
            logger.warning(
                "Hit concurrent aggregation limit with sequential processing. "
                "Falling back to batched processing with smaller chunks..."
            )
            return await _get_summary_statistics_batched(
                gee_interface, recipe, batch_size=2
            )
        else:
            raise


async def _get_summary_statistics_sequential(
    gee_interface: GEEInterface, recipe: Recipe
) -> RecipeStatsDict:
    """Sequential AOI processing (standard approach).

    Processes each AOI sequentially to avoid overwhelming GEE with concurrent operations.
    This is the primary method that should work for most cases.
    """

    if not recipe:
        raise ValueError("There is no recipe to get statistics from.")

    if not recipe.recipe_session_path:
        raise ValueError(
            "You can only export the dashboard data for the current recipe, load or create a recipe first in the recipe section"
        )

    seplan_model = recipe.seplan
    recipe_name = recipe.get_recipe_name()

    # Get all inputs from the model
    main_ee_features, secondary_ee_features = seplan_model.aoi_model.get_ee_features()
    main_ee_name = list(main_ee_features.keys())[0]

    ee_features = {**main_ee_features, **secondary_ee_features}

    # get list of benefits and names. This is used to get statistics.
    benefit_list = seplan_model.get_benefits_list()

    # List of masked out constraints and names
    constraint_list = seplan_model.get_masked_constraints_list()

    # Extract only the image from the constraint list and reduce to single mask
    mask_out_areas = reduce_constraints(constraint_list)

    # List of normalized costs and names
    cost_list = seplan_model.get_costs_list()

    # Get the restoration suitability index
    wlc_out = seplan_model.get_constraint_index()

    # Log computation details for debugging
    logger.info(
        f"Computing statistics for {len(ee_features)} AOI(s) with "
        f"{len(benefit_list)} benefit(s), {len(cost_list)} cost(s), "
        f"{len(constraint_list)} constraint(s)"
    )

    # Process each AOI sequentially to avoid concurrent aggregation limits
    # This prevents "Too many concurrent aggregations" errors with many layers
    result = {recipe_name: {}}

    for aoi_name, data in ee_features.items():
        logger.debug(f"Computing statistics for AOI: {aoi_name}")

        # Build the computation graph for this AOI
        aoi_dict = ee.Dictionary(
            {
                "suitability": get_image_stats(
                    wlc_out, mask_out_areas, data["ee_feature"]
                ),
                "benefit": [
                    get_image_mean(
                        image,
                        data["ee_feature"],
                        mask_out_areas,
                        name,
                        is_main_aoi(main_ee_name, aoi_name),
                    )
                    for image, name in benefit_list
                ],
                "cost": [
                    get_image_sum(image, data["ee_feature"], mask_out_areas, name)
                    for image, name in cost_list
                ],
                "constraint": [
                    get_image_percent_cover_pixelarea(image, data["ee_feature"], name)
                    for image, name in constraint_list
                ],
                "color": data["color"],
            }
        )

        # Process this AOI's statistics (one AOI at a time)
        result[recipe_name][aoi_name] = await gee_interface.get_info_async(aoi_dict)
        logger.debug(f"Completed statistics for AOI: {aoi_name}")

    logger.info(f"Successfully computed statistics for all {len(ee_features)} AOI(s)")
    return result


async def _get_summary_statistics_batched(
    gee_interface: GEEInterface, recipe: Recipe, batch_size: int = 3
) -> RecipeStatsDict:
    """Batched parallel processing fallback for very complex recipes.

    This method processes statistics in controlled parallel batches. Instead of running
    all operations at once or one-by-one, it runs a limited number concurrently (batch_size).
    This balances speed and reliability by staying under GEE's concurrent operation limits.

    Args:
        gee_interface: The GEE interface for async operations
        recipe: The recipe to compute statistics for
        batch_size: Number of operations to run concurrently per batch (default: 3)

    Returns:
        RecipeStatsDict with all computed statistics
    """

    if not recipe:
        raise ValueError("There is no recipe to get statistics from.")

    if not recipe.recipe_session_path:
        raise ValueError(
            "You can only export the dashboard data for the current recipe, load or create a recipe first in the recipe section"
        )

    seplan_model = recipe.seplan
    recipe_name = recipe.get_recipe_name()

    # Get all inputs from the model
    main_ee_features, secondary_ee_features = seplan_model.aoi_model.get_ee_features()
    main_ee_name = list(main_ee_features.keys())[0]

    ee_features = {**main_ee_features, **secondary_ee_features}

    # get list of benefits and names
    benefit_list = seplan_model.get_benefits_list()

    # List of masked out constraints and names
    constraint_list = seplan_model.get_masked_constraints_list()

    # Extract only the image from the constraint list and reduce to single mask
    mask_out_areas = reduce_constraints(constraint_list)

    # List of normalized costs and names
    cost_list = seplan_model.get_costs_list()

    # Get the restoration suitability index
    wlc_out = seplan_model.get_constraint_index()

    logger.info(
        f"[BATCHED MODE] Computing statistics for {len(ee_features)} AOI(s) with "
        f"{len(benefit_list)} benefit(s), {len(cost_list)} cost(s), "
        f"{len(constraint_list)} constraint(s) - parallel batch size: {batch_size}"
    )

    # Process each AOI separately to reduce concurrent operations
    result = {recipe_name: {}}

    for aoi_name, data in ee_features.items():
        logger.debug(f"[BATCHED] Processing AOI: {aoi_name}")

        aoi_result = {
            "suitability": None,
            "benefit": [],
            "cost": [],
            "constraint": [],
            "color": data["color"],
        }

        # Process suitability first
        suitability_dict = get_image_stats(wlc_out, mask_out_areas, data["ee_feature"])
        aoi_result["suitability"] = await gee_interface.get_info_async(suitability_dict)

        # Process benefits in parallel batches
        if benefit_list:
            logger.debug(
                f"[BATCHED] Processing {len(benefit_list)} benefits in parallel batches of {batch_size}"
            )
            for i in range(0, len(benefit_list), batch_size):
                batch = benefit_list[i : i + batch_size]

                # Create all tasks for this batch
                tasks = []
                for image, name in batch:
                    benefit_dict = get_image_mean(
                        image,
                        data["ee_feature"],
                        mask_out_areas,
                        name,
                        is_main_aoi(main_ee_name, aoi_name),
                    )
                    tasks.append(gee_interface.get_info_async(benefit_dict))

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for idx, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        _, name = batch[idx]
                        logger.error(
                            f"[BATCHED] Failed to process benefit '{name}': {result}"
                        )
                        error_msg = str(result).lower()
                        if "429" in error_msg or "resource_exhausted" in error_msg:
                            raise result
                        aoi_result["benefit"].append(
                            {name: {"values": {}, "total": [0], "error": str(result)}}
                        )
                    else:
                        aoi_result["benefit"].append(result)

                logger.debug(
                    f"[BATCHED] Completed benefit batch {i//batch_size + 1} ({len(batch)} items)"
                )

        if cost_list:
            logger.debug(
                f"[BATCHED] Processing {len(cost_list)} costs in parallel batches of {batch_size}"
            )
            for i in range(0, len(cost_list), batch_size):
                batch = cost_list[i : i + batch_size]

                tasks = []
                for image, name in batch:
                    cost_dict = get_image_sum(
                        image, data["ee_feature"], mask_out_areas, name
                    )
                    tasks.append(gee_interface.get_info_async(cost_dict))

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for idx, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        _, name = batch[idx]
                        logger.error(
                            f"[BATCHED] Failed to process cost '{name}': {result}"
                        )
                        error_msg = str(result).lower()
                        if "429" in error_msg or "resource_exhausted" in error_msg:
                            raise result
                        aoi_result["cost"].append(
                            {name: {"values": {}, "total": [0], "error": str(result)}}
                        )
                    else:
                        aoi_result["cost"].append(result)

                logger.debug(
                    f"[BATCHED] Completed cost batch {i//batch_size + 1} ({len(batch)} items)"
                )

        if constraint_list:
            logger.debug(
                f"[BATCHED] Processing {len(constraint_list)} constraints in parallel batches of {batch_size}"
            )
            for i in range(0, len(constraint_list), batch_size):
                batch = constraint_list[i : i + batch_size]

                tasks = []
                for image, name in batch:
                    constraint_dict = get_image_percent_cover_pixelarea(
                        image, data["ee_feature"], name
                    )
                    tasks.append(gee_interface.get_info_async(constraint_dict))

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for idx, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        _, name = batch[idx]
                        logger.error(
                            f"[BATCHED] Failed to process constraint '{name}': {result}"
                        )
                        error_msg = str(result).lower()
                        if "429" in error_msg or "resource_exhausted" in error_msg:
                            raise result
                        aoi_result["constraint"].append(
                            {name: {"values": {}, "total": [0], "error": str(result)}}
                        )
                    else:
                        aoi_result["constraint"].append(result)

                logger.debug(
                    f"[BATCHED] Completed constraint batch {i//batch_size + 1} ({len(batch)} items)"
                )

        result[recipe_name][aoi_name] = aoi_result
        logger.debug(f"[BATCHED] Completed AOI: {aoi_name}")

    logger.info(
        f"[BATCHED MODE] Successfully computed statistics for all {len(ee_features)} AOI(s)"
    )
    return result


def get_image_stats(image, mask, geom):
    """Computes the summary areas of suitability image based on region and masked land in HA.

    Args:
        image (eeimage): restoration suitability values 1 to 5
        mask (eeimage): mask of unsuitable land
        geom (eegeomerty): an earth engine geometry
        scale (int, optional): scale to reduce area by. Defaults to 100.

    Returns:
        eedictionary : a dictionary of suitability with the name of the region of intrest, list of values for each category, and total area.
    """
    # set masked areas as 6
    image = image.unmask(6)

    image = image.rename("image").round()

    areas = (
        ee.Image.pixelArea()
        .divide(10000)
        .addBands(image)
        .reduceRegion(
            reducer=ee.Reducer.sum().group(1, "image"),
            geometry=geom,
            scale=100,
            maxPixels=1e12,
        )
        .get("groups")
    )

    areas_list = ee.List(areas).map(lambda i: ee.Dictionary(i).get("sum"))
    total = areas_list.reduce(ee.Reducer.sum())

    out_dict = ee.Dictionary({"values": areas, "total": total})

    return out_dict


def get_image_percent_cover_pixelarea(
    image, aoi, name
) -> Dict[str, PercentageStatsDict]:
    """Get the percentage of masked area over the total."""
    # Be sure the mask is 0
    image = image.rename("image").unmask(0)

    areas = (
        ee.Image.pixelArea()
        .divide(10000)
        .addBands(image)
        .reduceRegion(
            reducer=ee.Reducer.sum().group(1, "image"),
            geometry=aoi,
            scale=100,
            maxPixels=1e12,
        )
        .get("groups")
    )
    areas = ee.List(areas)
    areas_list = areas.map(lambda i: ee.Dictionary(i).get("sum"))
    total = areas_list.reduce(ee.Reducer.sum())

    total_val = ee.Number(total)
    # get constraint area (e.g. groups class 0)
    # if the first group is 0 use it to calculate percent, else 0
    count_val = ee.Algorithms.If(
        ee.Algorithms.IsEqual(ee.Dictionary(areas.get(0)).get("image"), 0),
        areas_list.get(0),
        0,
    )

    percent = ee.Number(count_val).divide(total_val).multiply(100)

    value = ee.Dictionary({"values": {"percent": percent}, "total": [total_val]})

    return ee.Dictionary({name: value})


def get_image_mean(image, aoi, mask, name, main_aoi) -> Dict[str, MeanStatsDict]:
    """Computes the mean of image values not masked by constraints in relation to the total aoi.

    Returns dict name:{value:[],total:[]}.

    Args:
        image: The Earth Engine image to process
        aoi: Area of interest geometry
        mask: Mask to apply to the image
        name: Name for the output dictionary key
        main_aoi (bool): If the main aoi is being used, then the min and max values are also returned.

    Note: This function has been optimized to reduce the number of reduceRegion calls
    from 2 to 1 by reusing the masked mean calculation for the total value.
    """

    image = image.updateMask(mask)

    # Set the default values for the output
    result = ee.Dictionary(
        {
            "image_mean": 0,
            "image_max": 0,
            "image_min": 0,
        }
    )

    if main_aoi:
        image = image.rename(["image"])
        reducer = ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True)
    else:
        # if it is only one reducer, I have to rename the image.
        image = image.rename(["image_mean"])
        reducer = ee.Reducer.mean()

    # Single reduceRegion call instead of two
    result = result.combine(
        image.reduceRegion(
            reducer=reducer,
            geometry=aoi,
            scale=100,
            maxPixels=1e13,
        )
    )

    from_ = ["image_mean", "image_max", "image_min"]
    to_ = ["mean", "max", "min"]

    values: MeanStatsValues = result.rename(from_, to_)

    value = ee.Dictionary({"total": [result.get("image_mean")], "values": values})

    return ee.Dictionary({name: value})


def get_image_sum(image, aoi, mask, name) -> Dict[str, SumStatsDict]:
    """Computes the sum of image values not masked by constraints in relation to the total aoi.

    returns dict name:{value:[],total:[]}.
    """
    area_ha = (
        ee.Image.pixelArea()
        .divide(10000)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=aoi,
            scale=100,
            maxPixels=1e13,
        )
        .get("area")
    )

    sum_img = image.updateMask(mask).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi,
        scale=100,
        maxPixels=1e13,
    )

    total_img = image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi,
        scale=100,
        maxPixels=1e13,
    )

    value = ee.Dictionary(
        {
            "values": {"sum": ee.Number(sum_img.values().get(0)).divide(area_ha)},
            "total": [ee.Number(total_img.values().get(0)).divide(area_ha)],
        }
    )

    return ee.Dictionary({name: value})
