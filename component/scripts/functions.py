import ee
import json
from traitlets import Any, HasTraits

from component import parameter as cp
from component import model

ee.Initialize()

####################################################
###   default parameters of the singleton   ########
####################################################

# find the criteria name of every range slider and bool
range_constraint_names = [
    i for i in cp.criterias if cp.criterias[i]["content"] == "RANGE"
]
bool_constraint_names = [
    i for i in cp.criterias if cp.criterias[i]["content"] == "BINARY"
]

####################################################


def wlc(layer_list, constraints, priorities, aoi_ee):
    """
    Compute the resoration suitability indocator over the specified AOI
    the computation will take into account all the parameters specified by the user in the app

    Args:
        layer_list (dict): the list of layers items
        constraints (str): a str json formatted list of constraints. Use the formatting specified in the QuestionModel
        priorities (str): a str json formatted list of priorities. Use the formatting specified in the QuestionModel

    Return:
        (ee.Image): the restoration suitability index
    """
    # load the json strings
    constraints = json.loads(constraints)
    priorities = json.loads(priorities)

    # load layers and create eeimages
    benefit_list = [
        i for i in layer_list if i["theme"] == "benefits" and priorities[i["id"]] != 0
    ]
    list(
        map(
            lambda i: i.update({"eeimage": ee.Image(i["layer"]).unmask()}), benefit_list
        )
    )

    risk_list = [i for i in layer_list if i["theme"] == "risks"]
    list(map(lambda i: i.update({"eeimage": ee.Image(i["layer"])}), risk_list))

    cost_list = [i for i in layer_list if i["theme"] == "costs"]
    list(map(lambda i: i.update({"eeimage": ee.Image(i["layer"]).unmask()}), cost_list))

    # constraint_list, initialize with constant value 1
    # meaning that for all layer nothing is masked
    constraint_list = [i for i in layer_list if i["theme"] == "constraint"]
    list(map(lambda i: i.update({"eeimage": ee.Image.constant(1)}), constraint_list))
    constraint_list = set_constraints(constraints, constraint_list)

    # normalize the benefits on the aoi extends using the quintile method
    benefit_list = normalize_benefits(benefit_list, aoi_ee, "quintile")

    # normalize benefit weights to 0 - 1
    sum_weights = sum(priorities[i["id"]] for i in benefit_list)
    list(
        map(
            lambda i: i.update(
                {"norm_weight": round((priorities[i["id"]] / sum_weights), 5)}
            ),
            benefit_list,
        )
    )

    # calc wlc image
    exp, exp_dict = get_expression(benefit_list, cost_list, constraint_list)
    wlc_image = ee.Image.constant(1).expression(exp, exp_dict)

    # rescale wlc image from to
    wlc_image = (
        _percentile(wlc_image, aoi_ee, scale=10000, percentile=[3, 97])
        .multiply(4)
        .add(1)
    )

    # rather than clipping paint wlc to region
    wlc_out = ee.Image().float()
    wlc_out = (
        wlc_out.paint(ee.FeatureCollection(aoi_ee), 0)
        .where(wlc_image, wlc_image)
        .selfMask()
    )

    return wlc_out, benefit_list, constraint_list, cost_list


def set_constraints(constraints, constraint_list):
    """
    Update the constraint_layers list with filtered ee.Images according to user parameters

    Args:
        constraints (dict): a str json formatted list of constraints. Use the formatting specified in the QuestionModel
        constraint_list (list): the list of all the constraint layer. each layer is represented by a dict : {'eeimage': dataset}

    Return:
        (list): the updated version of the constraints_layers
    """

    # loop through all the constraint in the json list
    for name in constraints:

        value = constraints[name]

        # skip if the constraint is disabled
        if value == None or value == -1:
            continue

        # get the constraint
        constraint_layer = get_layer(name, constraint_list)

        # boolean masking lc
        # use the value associated to the name to build the mask image
        if name in cp.landcover_default_cat and isinstance(value, bool):
            constraint_list.append(
                get_cat_constraint(
                    cp.landcover_default_cat[name],
                    value,
                    name,
                    constraint_layer["layer"],
                )
            )

        # range constraints (slope, rainfall, etc...)
        elif name in range_constraint_names:
            constraint_layer.update(
                eeimage=get_range_constraint(value, constraint_layer["layer"])
            )

        # the rest of the bool values (land cover have already been handle I can safely use the bool list)
        elif name in bool_constraint_names:
            constraint_layer.update(
                ee_image=get_bool_constraint(value, constraint_layer["layer"])
            )

    # add the default geographic constraint
    default_geographic = next(
        item
        for item in constraint_list
        if item["name"] == "Current tree cover less than potential"
    )
    default_geographic.update(eeimage=ee.Image(default_geographic["layer"]))

    return constraint_list


def get_layer(layer_name, constraint_list):
    """Return the layer dict

    Args:
        layer_name(str): the layer name (with spaces)
        constraint_list(list of dict): the list of each layer and it's eeimage

    Return:
        (dict): the layer dict"""

    # for all land cover constraints we use the same layer
    if layer_name in cp.landcover_default_cat:
        constraint_layer = next(
            i for i in constraint_list if i["name"] == "Current land cover"
        )

    # else use the one that have the same name
    else:
        constraint_layer = next(i for i in constraint_list if i["name"] == layer_name)

    return constraint_layer


def get_cat_constraint(cat_id, value, name, layer_id):
    """
    Return fully defined layer dict for the constraint list

    Args:
        cat_id (int): the category number to mask in the landcover image
        value (bool): a bool value to mask the category. True: mask it, False: keep only this one
        name (str): the constraint name
        layer_id (str): the gee layer id

    Return:
        (dict): the fully qualified layer dict
    """

    # read the ee image and mask it according to the value
    image = ee.Image(layer_id).select("discrete_classification")
    image = image.neq(cat_id) if value else image.eq(cat_id)

    return {"theme": "constraints", "name": name, "eeimage": image}


def get_range_constraint(values, layer_id):
    """
    set a contraint in the provided layer list using the name provided by the criteria and the values provided by the user.
    The function will find the layer in the list and update the eeimage mask

    Args:
        values (list): the min and max value of the specified range
        layer_id (str): the gee layer id

    Return:
        (ee.Image): the masked gee image
    """

    # extract an ee.Image
    image = ee.Image(layer_id)

    # filter the image according to min and max values set by the user
    image = image.gt(values[0]).And(image.lt(values[1]))

    return image


def get_bool_constraint(value, layer_id):
    """
    set a contraint in the provided layer list using the name provided by the criteria and the value provided by the user.
    The function will find the layer in the list and update the eeimage mask

    Args:
        value (bool): a bool value to mask the category. True: mask it, False: keep only this one
        layer_id (str): the gee layer id

    Return:
        (ee.Image): the masked gee image
    """

    # extract an ee.Image
    image = ee.Image(layer_id)

    # filter the image according to the value provided by the user
    image = image.eq(0) if value else image.eq(1)

    return image


def normalize_benefits(benefit_list, ee_aoi, method="minmax"):
    """
    Normalize each benefits using the provided method

    Args:
        benefit_list (list): the list of the benefit
        ee_aoi (ee.FeatureCollection): the aoi as an ee.FeatureCollection
        method (str, optional): the method to use to normalize


    Return:
        the normalized benefit_list
    """

    # update the layer images
    for layer in benefit_list:
        layer.update(eeimage=normalize_image(layer, ee_aoi, method))

    return benefit_list


def _minmax(ee_image, ee_aoi, scale=10000):
    """use the minmax normalization"""

    mmvalues = ee_image.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=ee_aoi.geometry(),
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=4,
    )

    band_name = ee.String(ee_image.bandNames().get(0))
    key_min = band_name.cat("_min")
    key_max = band_name.cat("_max")

    img_min = ee.Number(mmvalues.get(key_min))
    img_max = ee.Number(mmvalues.get(key_max))

    return ee_image.unitScale(img_min, img_max).float()


def _percentile(ee_image, ee_aoi, scale=10000, percentile=[3, 97]):
    """Use the percentile normalization"""

    tmp_ee_image = ee_image.rename("img")

    percents = tmp_ee_image.reduceRegion(
        geometry=ee_aoi.geometry(),
        reducer=ee.Reducer.percentile(percentiles=percentile),
        scale=scale,
    )

    img_low = ee.Number(percents.get(f"img_p{percentile[0]}"))
    img_high = ee.Number(percents.get(f"img_p{percentile[1]}")).add(0.1e-13)

    return ee_image.unitScale(img_low, img_high).clamp(0, 1)


def _quintile(ee_image, ee_aoi, scale=100):
    """use quintile normailzation"""

    quintile_collection = ee_image.reduceRegions(
        collection=ee_aoi,
        reducer=ee.Reducer.percentile(
            percentiles=[20, 40, 60, 80],
            outputNames=["low", "lowmed", "highmed", "high"],
        ),
        tileScale=2,
        scale=scale,
    )

    # only use features that have non null quintiles
    valid_quintiles = quintile_collection.filter(
        ee.Filter.notNull(["high", "low", "lowmed", "highmed"])
    )
    vaild_quintiles_list = valid_quintiles.toList(valid_quintiles.size())

    # catch regions where input region is null for user info (debug)
    # invalid_regions = quintile_collection.filter(ee.Filter.notNull(['high','low','lowmed','highmed']).Not())

    def conditions(feature):

        feature = ee.Feature(feature)

        quintiles = ee.Image().byte()
        quintiles = quintiles.paint(ee.FeatureCollection(feature), 0)

        low = ee.Number(feature.get("low"))
        lowmed = ee.Number(feature.get("lowmed"))
        highmed = ee.Number(feature.get("highmed"))
        high = ee.Number(feature.get("high"))

        out = (
            quintiles.where(ee_image.lte(low), 1)
            .where(ee_image.gt(low).And(ee_image.lte(lowmed)), 2)
            .where(ee_image.gt(lowmed).And(ee_image.lte(highmed)), 3)
            .where(ee_image.gt(highmed).And(ee_image.lte(high)), 4)
            .where(ee_image.gt(high), 5)
        )

        return out

    quintile_image = ee.ImageCollection(vaild_quintiles_list.map(conditions)).mosaic()

    return quintile_image


def normalize_image(layer, ee_aoi, method="mixmax"):
    """
    Return the normalize image of a set layer using the provided method

    Args:
        layer (dict): the fully qualified layer dict
        ee_aoi (ee.FeatureCollection): the defined aoi
        method (str): the method to use
    """

    normalize = {"minmax": _minmax, "quintile": _quintile}

    return normalize[method](ee.Image(layer["layer"]), ee_aoi)


def get_expression(benefit_list, cost_list, constraint_list):

    fdict_bene, idict_bene, benefits_exp = get_benefit_expression(benefit_list)
    idict_cost, costs_exp = get_cost_expression(cost_list)
    idict_cons, constraint_exp = get_constraint_expression(constraint_list)

    expression_dict = {**fdict_bene, **idict_bene, **idict_cost, **idict_cons}
    expression = f"( ( {benefits_exp} / {costs_exp} ) * {constraint_exp} )"

    return expression, expression_dict


def get_benefit_expression(benefit_list):

    # build expressions for benefits
    fdict_bene = {f"f{i}": e["norm_weight"] for i, e in enumerate(benefit_list)}
    idict_bene = {f"b{i}": e["eeimage"] for i, e in enumerate(benefit_list)}

    exp_bene = [f"(f{i}*b{i})" for i, e in enumerate(benefit_list)]

    benefits_exp = f"({'+'.join(exp_bene)})"

    return fdict_bene, idict_bene, benefits_exp


def get_cost_expression(cost_list):

    idict = {f"c{i}": e["eeimage"] for i, e in enumerate(cost_list)}
    exp = [f"(c{i})" for i, e in enumerate(cost_list)]
    exp_string = f"({'+'.join(exp)})"

    return idict, exp_string


def get_constraint_expression(constraint_list):

    idict = {f"cn{i}": e["eeimage"] for i, e in enumerate(constraint_list)}
    exp = [f"(cn{i})" for i, e in enumerate(constraint_list)]
    exp_string = f"({'*'.join(exp)})"

    return idict, exp_string
