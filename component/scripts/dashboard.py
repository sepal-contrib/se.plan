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
def get_benefits(layer_list:list, geom:ee.Geometry, constraint_mask:ee.Image)->ee.Dictionary:
    
    all_benefits_layers = [i for i in layer_list if i["theme"] == "benefit"]
    fn_all_benefit = lambda i: i.update({"eeimage": ee.Image(i["layer"]).unmask()})
    list(map(fn_all_benefit, all_benefits_layers))

    fn_benefits = lambda i: get_image_mean(i["eeimage"], geom, i["id"], constraint_mask)

    return ee.Dictionary(
        {"benefit": list(map(fn_benefits, all_benefits_layers))}
    )

def get_costs(costs:list, geom:ee.Geometry, constraint_mask:ee.Image)->ee.Dictionary:
    fn_costs = lambda i: get_image_sum(i["eeimage"], geom, i["id"], constraint_mask)
    return ee.Dictionary({"cost": list(map(fn_costs, costs))})

def get_constraints(constraints:list, geom:ee.Geometry, constraint_mask:ee.Image)->ee.Dictionary:
    fn_constraint = lambda i: get_image_percent_cover_pixelarea(
        i["eeimage"], geom, i["id"]
    )
    return ee.Dictionary(
        {"constraint": list(map(fn_constraint, constraints))}
    )

def make_mask_constraints(constraints:list)->ee.Image:
    return  ee.ImageCollection(
        list(map(lambda i: ee.Image(i["eeimage"]).rename("c").byte(), constraints))
    ).min()

def get_summary_statistics(wlc_outputs, name, geom, layer_list, client_side):
    """returns summarys for the dashboard."""

    # unpack restoration suitability results
    wlc, benefits, constraints, costs = wlc_outputs

    #maske constraints mask to restrict summary to proper areas     
    constraint_mask = make_mask_constraints(constraints)

    # restoration potential stats
    wlc_summary = get_image_stats(wlc, name, constraint_mask, geom)

    # benefits
    benefits_out = get_benefits(layer_list, geom, constraint_mask)
    
    # costs 
    costs_out = get_costs(costs, geom, constraint_mask)

    # constraints
    constraints_out =  get_constraints(constraints, geom, constraint_mask)

    # combine the result
    result = (
        wlc_summary.combine(benefits_out).combine(costs_out).combine(constraints_out)
    )
    
    if client_side:
        result = ee.String.encodeJSON(result).getInfo()
    
    return result


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
        json_themes_values (dict):Theme formatted dictionay of {THEME: {LAYER: 'total':float, 'values':[float]}}
    """
    tmp_dict = {}
    names = []

    for aoi in stats:
        # read information as they are stored as a string
        features = json.loads(aoi)

        # remove suitability from the start
        features = {k: v for k, v in features.items() if k != "suitability"}

        for theme, layers in features.items():
            # add the theme to the keys if necessary (during the first loop)
            theme in tmp_dict or tmp_dict.update({theme: {}})

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


def get_stats(wlc_outputs, layer_model, aoi_model, features, names):

    # create the final featureCollection
    # the first one is the aoi and the rest are sub areas
    ee_aoi_list = [aoi_model.feature_collection]
    for feat in features["features"]:
        ee_aoi_list.append(geemap.geojson_to_ee(feat))

    # create the stats dictionnary
    stats = [
        get_summary_statistics(wlc_outputs, names[i], geom, layer_model.layer_list, True)
        for i, geom in enumerate(ee_aoi_list)
    ]

    area_dashboard = get_area_dashboard(stats)
    theme_dashboard = get_theme_dashboard(stats)

    return area_dashboard, theme_dashboard


def dictionaryToFeatures(results:ee.List,category:str,type_feat:str)->ee.FeatureCollection:
    results = ee.List(results)
    def parseResults(result):
        result = ee.Dictionary(result)
        result_key = result.keys().get(0)
        main_dict = ee.Dictionary(result.get(result_key))
        tmp_dict = {
          'category':category,
          'type': type_feat,
          'name': result_key,
          'total': ee.List(main_dict.get('total')).get(0),
          'value': ee.List(main_dict.get('values')).get(0),

        }
        return ee.Feature(ee.Geometry.Point([0,0])).setMulti(tmp_dict);
      
    features = results.map(parseResults);
  
    return ee.FeatureCollection(features);



def suitibilityToFeatures(suitability:ee.Dictionary)->ee.FeatureCollection:
    suitability = ee.Dictionary(suitability)
    suit_key = suitability.keys().get(0)
    main_dict = ee.Dictionary(suitability.get(suit_key))
    tmp_dict = {
        'category':'suitability',
        'type':'area',
        'name': suit_key,
        'total': main_dict.get('total'),
        'value': main_dict.get('total'),
    }
    
    area_total = ee.Feature(ee.Geometry.Point([0,0])).setMulti(tmp_dict)

    map_values = main_dict.get('values')
    def parse_results(result):
        result = ee.Dictionary(result)
        sub_dict = {
          'category':'suitability',
          'type':'area',
          'name': result.get('image'),
          'value':result.get('sum'),
          }
        return ee.Feature(ee.Geometry.Point([0,0])).setMulti(sub_dict)

    map_feats = ee.List(map_values).map(parse_results)
    return ee.FeatureCollection(map_feats.add(area_total))

def dashboard_data_to_fc(dashboard_data:ee.Dictionary)->ee.FeatureCollection:
    benefits = dashboard_data.get('benefit')
    constraints = dashboard_data.get('constraint')
    costs = dashboard_data.get('cost')
    suitability = dashboard_data.get('suitability')
    
    suitibilityFeatures = suitibilityToFeatures(suitability)
    benefitFeatures = dictionaryToFeatures(benefits,'benefit','mean')
    constraintFeatures = dictionaryToFeatures(constraints,'constraint','area')
    costFeatures = dictionaryToFeatures(costs,'cost','sum')
    
    fin = ee.FeatureCollection([suitibilityToFeatures(suitability),
        dictionaryToFeatures(benefits,'benefit','mean'),
        dictionaryToFeatures(constraints,'constraint','area'),
        dictionaryToFeatures(costs,'cost','sum')]).flatten()
    return fin