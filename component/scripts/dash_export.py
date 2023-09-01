"""Functions that are only required when using the batch export notebook."""

import ee


def dictionaryToFeatures(
    results: ee.List, category: str, type_feat: str
) -> ee.FeatureCollection:
    results = ee.List(results)

    def parseResults(result):
        result = ee.Dictionary(result)
        result_key = result.keys().get(0)
        main_dict = ee.Dictionary(result.get(result_key))
        tmp_dict = {
            "category": category,
            "type": type_feat,
            "name": result_key,
            "total": ee.List(main_dict.get("total")).get(0),
            "value": ee.List(main_dict.get("values")).get(0),
        }
        return ee.Feature(ee.Geometry.Point([0, 0])).setMulti(tmp_dict)

    features = results.map(parseResults)

    return ee.FeatureCollection(features)


def suitibilityToFeatures(suitability: ee.Dictionary) -> ee.FeatureCollection:
    suitability = ee.Dictionary(suitability)
    suit_key = suitability.keys().get(0)
    main_dict = ee.Dictionary(suitability.get(suit_key))
    tmp_dict = {
        "category": "suitability",
        "type": "area",
        "name": suit_key,
        "total": main_dict.get("total"),
        "value": main_dict.get("total"),
    }

    area_total = ee.Feature(ee.Geometry.Point([0, 0])).setMulti(tmp_dict)

    map_values = main_dict.get("values")

    def parse_results(result):
        result = ee.Dictionary(result)
        sub_dict = {
            "category": "suitability",
            "type": "area",
            "name": result.get("image"),
            "value": result.get("sum"),
        }
        return ee.Feature(ee.Geometry.Point([0, 0])).setMulti(sub_dict)

    map_feats = ee.List(map_values).map(parse_results)
    return ee.FeatureCollection(map_feats.add(area_total))


def dashboard_data_to_fc(dashboard_data: ee.Dictionary) -> ee.FeatureCollection:
    benefits = dashboard_data.get("benefit")
    constraints = dashboard_data.get("constraint")
    costs = dashboard_data.get("cost")
    suitability = dashboard_data.get("suitability")

    suitibilityFeatures = suitibilityToFeatures(suitability)
    benefitFeatures = dictionaryToFeatures(benefits, "benefit", "mean")
    constraintFeatures = dictionaryToFeatures(constraints, "constraint", "area")
    costFeatures = dictionaryToFeatures(costs, "cost", "sum")

    fin = ee.FeatureCollection(
        [suitibilityFeatures, benefitFeatures, constraintFeatures, costFeatures]
    ).flatten()

    return fin
