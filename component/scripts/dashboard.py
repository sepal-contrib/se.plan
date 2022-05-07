import ee
import json
from datetime import datetime as dt
import os

import geemap


def _quintile(image, geometry, scale=100):
    """Computes standard quintiles of an image based on an aoi. returns feature collection with quintiles as propeties"""

    quintile_collection = image.reduceRegion(
        geometry=geometry,
        reducer=ee.Reducer.percentile(
            percentiles=[20, 40, 60, 80],
            outputNames=["low", "lowmed", "highmed", "high"],
        ),
        tileScale=2,
        scale=scale,
        maxPixels=1e13,
    )

    return quintile_collection


def get_areas(image, geometry, scale=100):
    image = image.rename("image").round()
    pixelArea = ee.Image.pixelArea().divide(10000)
    reducer = ee.Reducer.sum().group(1, "image")

    areas = (
        pixelArea.addBands(image)
        .reduceRegion(reducer=reducer, geometry=geometry, scale=100, maxPixels=1e12)
        .get("groups")
    )

    areas_list = ee.List(areas).map(lambda i: ee.Dictionary(i).get("sum"))

    total = areas_list.reduce(ee.Reducer.sum())

    sum_img = image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=100,
        maxPixels=1e13,
    )

    return areas, total


def get_image_stats(image, name, mask, geom, scale=100):
    """Computes the summary areas of suitability image based on region and masked land in HA.

    Args:
        image (eeimage): restoration suitability values 1 to 5
        name (string): name of the area of interest
        mask (eeimage): mask of unsuitable land
        geom (eegeomerty): an earth engine geometry
        scale (int, optional): scale to reduce area by. Defaults to 100.

    Returns:
        eedictionary : a dictionary of suitability with the name of the region of intrest, list of values for each category, and total area.
    """

    image = image.where(mask.eq(0), 6)

    list_values, total = get_areas(image, geom)

    out_dict = ee.Dictionary(
        {"suitability": {name: {"values": list_values, "total": total}}}
    )

    return out_dict


def get_aoi_count(aoi, name):

    count_aoi = (
        ee.Image.constant(1)
        .rename(name)
        .reduceRegion(
            reducer=ee.Reducer.count(), geometry=aoi, scale=100, maxPixels=1e13
        )
    )

    return count_aoi


def get_image_percent_cover_pixelarea(image, aoi, name):

    image = image.rename("image")
    pixelArea = ee.Image.pixelArea().divide(10000)
    reducer = ee.Reducer.sum().group(1, "image")

    areas = (
        pixelArea.addBands(image)
        .reduceRegion(reducer=reducer, geometry=aoi, scale=100, maxPixels=1e12)
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


def get_image_percent_cover(image, aoi, name):
    """computes the percent coverage of a constraint in relation to the total aoi. returns dict name:{value:[],total:[]}"""

    count_img = (
        image.Not()
        .selfMask()
        .reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=aoi,
            scale=100,
            maxPixels=1e13,
        )
    )

    total_img = image.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=aoi,
        scale=100,
        maxPixels=1e13,
    )

    total_val = ee.Number(total_img.values().get(0))
    count_val = ee.Number(count_img.values().get(0))

    percent = count_val.divide(total_val).multiply(100)

    value = ee.Dictionary({"values": [percent], "total": [total_val]})

    return ee.Dictionary({name: value})


def get_image_mean(image, aoi, name, mask):
    """computes the sum of image values not masked by constraints in relation to the total aoi. returns dict name:{value:[],total:[]}"""

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

    return ee.Dictionary({name: value})


def get_image_sum(image, aoi, name, mask):
    """computes the sum of image values not masked by constraints in relation to the total aoi. returns dict name:{value:[],total:[]}"""

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

    value = ee.Dictionary({"values": sum_img.values(), "total": total_img.values()})

    return ee.Dictionary({name: value})


def get_summary_statistics(wlc_outputs, name, geom, layer_list):
    """returns summarys for the dashboard."""

    # restoration suitability
    wlc, benefits, constraints, costs = wlc_outputs
    mask = ee.ImageCollection(
        list(map(lambda i: ee.Image(i["eeimage"]).rename("c").byte(), constraints))
    ).min()

    # restoration pot. stats
    wlc_summary = get_image_stats(wlc, name, mask, geom)

    # benefits
    # remake benefits from layerlist as original output are in quintiles
    all_benefits_layers = [i for i in layer_list if i["theme"] == "benefit"]
    fn_all_benefit = lambda i: i.update({"eeimage": ee.Image(i["layer"]).unmask()})
    list(map(fn_all_benefit, all_benefits_layers))

    fn_benefits = lambda i: get_image_mean(i["eeimage"], geom, i["id"], mask)
    benefits_out = ee.Dictionary(
        {"benefit": list(map(fn_benefits, all_benefits_layers))}
    )

    # costs
    fn_costs = lambda i: get_image_sum(i["eeimage"], geom, i["id"], mask)
    costs_out = ee.Dictionary({"cost": list(map(fn_costs, costs))})

    # constraints
    fn_constraint = lambda i: get_image_percent_cover_pixelarea(
        i["eeimage"], geom, i["id"]
    )
    constraints_out = ee.Dictionary(
        {"constraint": list(map(fn_constraint, constraints))}
    )

    # combine the result
    result = (
        wlc_summary.combine(benefits_out).combine(costs_out).combine(constraints_out)
    )

    return ee.String.encodeJSON(result).getInfo()


def get_area_dashboard(stats):

    tmp = {}
    for i in stats:
        suitability_i = json.loads(i)
        tmp.update(suitability_i["suitability"])

    return tmp


def get_theme_dashboard(stats):
    """Prepares the dashboard export for plotting on the theme area of the dashboard by appending values for each layer and AOI into a single dictionary.
    args:
        json_dashboard (list): List of string dicts. Each feature with summary values for benefits, costs, risks and constraints.

    returns:
        json_thmemes_values (dict):Theme formatted dictionay of {THEME: {LAYER: 'total':float, 'values':[float]}}
    """
    tmp_dict = {}
    names = []

    for feature in stats:
        feature = json.loads(feature)
        for k, layers in feature.items():
            if k not in tmp_dict:
                tmp_dict[k] = {}
            for layer in layers:
                if isinstance(layer, str):
                    names.append(layer)
                    continue
                layer_name = next(iter(layer))
                layer_value = layer[layer_name]["values"][0]
                layer_total = layer[layer_name]["total"][0]

                if layer_name not in tmp_dict[k]:
                    tmp_dict[k][layer_name] = {"values": [], "total": 0}
                    tmp_dict[k][layer_name]["values"].append(layer_value)
                    tmp_dict[k][layer_name]["total"] = layer_total
                else:
                    tmp_dict[k][layer_name]["values"].append(layer_value)
                    tmp_dict[k][layer_name]["total"] = max(
                        layer_total, tmp_dict[k][layer_name]["total"]
                    )
    tmp_dict["names"] = names
    tmp_dict.pop("suitability", None)

    return tmp_dict


def get_stats(wlc_outputs, layer_model, aoi_model, features, names):

    # create the final featureCollection
    # the first one is the aoi and the rest are sub areas
    ee_aoi_list = [aoi_model.feature_collection]
    for feat in features["features"]:
        ee_aoi_list.append(geemap.geojson_to_ee(feat))

    # create the stats dictionnary
    stats = [
        get_summary_statistics(wlc_outputs, names[i], geom, layer_model.layer_list)
        for i, geom in enumerate(ee_aoi_list)
    ]

    area_dashboard = get_area_dashboard(stats)
    theme_dashboard = get_theme_dashboard(stats)

    return area_dashboard, theme_dashboard
