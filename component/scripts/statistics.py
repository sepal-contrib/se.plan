from typing import Dict, List

import ee

from component.scripts.seplan import Seplan, reduce_constraints


def get_summary_statistics(seplan_model: Seplan) -> List[Dict]:
    """Returns summary statistics using seplan inputs.

    The statistics will be later parsed to be displayed in the dashboard.
    """
    # Get all inputs from the model
    ee_features = seplan_model.aoi_model.get_ee_features()

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

    return [
        ee.Dictionary(
            {
                aoi_name: {
                    "suitability": get_image_stats(
                        wlc_out, mask_out_areas, data["ee_feature"]
                    ),
                    "benefit": [
                        get_image_mean(image, data["ee_feature"], mask_out_areas, name)
                        for image, name in benefit_list
                    ],
                    "cost": [
                        get_image_sum(image, data["ee_feature"], mask_out_areas, name)
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
            }
        ).getInfo()
        for aoi_name, data in ee_features.items()
    ]


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


def get_image_percent_cover_pixelarea(image, aoi, name):
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

    value = ee.Dictionary({"values": [percent], "total": [total_val]})

    return ee.Dictionary({name: value})


def get_image_mean(image, aoi, mask, name):
    """Computes the sum of image values not masked by constraints in relation to the total aoi. returns dict name:{value:[],total:[]}."""
    mean_img = image.updateMask(mask).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=100,
        maxPixels=1e13,
    )

    total_img = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=100,
        maxPixels=1e13,
    )

    value = ee.Dictionary({"values": mean_img.values(), "total": total_img.values()})

    # return ee.Dictionary({image.get("name").getInfo(): value})
    return ee.Dictionary({name: value})


def get_image_sum(image, aoi, mask, name):
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
            "values": [ee.Number(sum_img.values().get(0)).divide(area_ha)],
            "total": [ee.Number(total_img.values().get(0)).divide(area_ha)],
        }
    )

    # return ee.Dictionary({image.get("name").getInfo(): value})
    return ee.Dictionary({name: value})


def parse_theme_stats(stats: List[Dict]):
    """Prepares the dashboard export for plotting on the theme area of the dashboard by appending values for each layer and AOI into a single dictionary.

    Args:
        stats (list): List of string dicts. Each feature with summary values for benefits, costs, risks and constraints.

    Returns:
        json_themes_values (dict):Theme formatted dictionay of {THEME: {LAYER: 'total':float, 'values':[float]}}
    """
    tmp_dict = {}

    for aoi_data in stats:
        # remove suitability from the start
        features = {
            k: v
            for k, v in list(aoi_data.values())[0].items()
            if k not in ["suitability", "color"]
        }

        for theme, layers in features.items():
            # add the theme to the keys if necessary (during the first loop)
            tmp_dict.setdefault(theme, {})

            # first loop to sum all the values related to the same layer (e.g. land_cover)
            # each layer is tored in a dict: {lid: {"value": xx, "total": cc}}
            d = {}
            for layer in layers:
                lid = next(iter(layer))
                stat = layer[lid]
                lid in d or d.update({lid: {"values": 0, "total": 0}})
                v = stat["values"][0] if stat["values"][0] is not None else 0
                d[lid]["values"] += v
                d[lid]["layer_total"] = stat["total"][0]

            # second loop to write down everything in the tmp_dict
            for lid, stat in d.items():
                lid in tmp_dict[theme] or tmp_dict[theme].update(
                    {lid: {"values": [], "total": 0}}
                )
                tmp_dict[theme][lid]["values"].append(stat["values"])
                tmp_dict[theme][lid]["total"] = max(
                    stat["total"], tmp_dict[theme][lid]["total"]
                )

    return tmp_dict
