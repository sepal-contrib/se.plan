from typing import Dict, List
import ee

from component.model.recipe import Recipe
from component.scripts.seplan import Seplan, reduce_constraints
from component.types import (
    MeanStatsDict,
    MeanStatsValues,
    PercentageStatsDict,
    RecipeStatsDict,
    SumStatsDict,
)


def is_main_aoi(main_aoi_name, aoi_name) -> bool:
    """Check if the aoi is the main aoi."""
    return main_aoi_name == aoi_name


def get_summary_statistics(recipe: Recipe) -> RecipeStatsDict:
    """Returns summary statistics using seplan inputs.

    The statistics will be later parsed to be displayed in the dashboard.
    """

    if not recipe:
        raise ValueError("There is no recipe to get statistics from.")

    seplan_model = recipe.seplan
    recipe_name = recipe.get_recipe_name()

    # Get all inputs from the model
    main_ee_features, secondary_ee_features = seplan_model.aoi_model.get_ee_features()
    main_ee_name = list(main_ee_features.keys())[0]

    ee_features = {**main_ee_features, **secondary_ee_features}

    # get list of benefits and names. Tihs is used to get statistics.
    benefit_list = seplan_model.get_benefits_list()

    # List of masked out constraints and names
    constraint_list = seplan_model.get_masked_constraints_list()

    # Extract only the image from the constraint list and reduce to single mask
    mask_out_areas = reduce_constraints(constraint_list)

    # List of normalized costs and names
    cost_list = seplan_model.get_costs_list()

    # Get the restoration suitability index
    wlc_out = seplan_model.get_constraint_index()

    return (
        ee.Dictionary(
            {
                recipe_name: ee.Dictionary(
                    {
                        aoi_name: ee.Dictionary(
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
                                    get_image_sum(
                                        image, data["ee_feature"], mask_out_areas, name
                                    )
                                    for image, name in cost_list
                                ],
                                "constraint": [
                                    get_image_percent_cover_pixelarea(
                                        image, data["ee_feature"], name
                                    )
                                    for image, name in constraint_list
                                ],
                                "color": data["color"],
                            }
                        )
                        for aoi_name, data in ee_features.items()
                    }
                )
            }
        )
    ).getInfo()


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
    """Computes the sum of image values not masked by constraints in relation to the total aoi. returns dict name:{value:[],total:[]}.

    Args:

        main_aoi (bool): If the main aoi is being used, then the min and max values are also returned.

    """

    reducer = ee.Reducer.mean()
    image = image.updateMask(mask)

    if main_aoi:
        image = image.rename(["image"])
        reducer = reducer.combine(ee.Reducer.minMax(), sharedInputs=True)
    else:
        # if it is only one reducer, I have to rename the image.
        image = image.rename(["image_mean"])

    result = image.reduceRegion(
        reducer=reducer,
        geometry=aoi,
        scale=100,
        maxPixels=1e13,
    )

    if not main_aoi:
        # Just add dummy data to be consistent with the output
        result = result.combine({"image_max": 0, "image_min": 0}, overwrite=False)

    total_img = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=100,
        maxPixels=1e13,
    )

    from_ = ["image_mean", "image_max", "image_min"]
    to_ = ["mean", "max", "min"]

    values: MeanStatsValues = result.rename(from_, to_)

    value = ee.Dictionary({"total": total_img.values(), "values": values})

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

    # return ee.Dictionary({image.get("name").getInfo(): value})
    return ee.Dictionary({name: value})
