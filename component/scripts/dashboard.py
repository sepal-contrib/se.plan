import ee
import json

# dev
from test_gee_compute_params import *
from functions import *
def _quintile(image, featurecollection, scale=100):
    """ computes standar quintiles of an image based on an aoi. returns feature collection with quintiles as propeties """ 
    quintile_collection = image.reduceRegions(collection=featurecollection, 
    reducer=ee.Reducer.percentile(percentiles=[20,40,60,80],outputNames=['low','lowmed','highmed','high']), 
    tileScale=2,scale=scale)

    return quintile_collection
def _count_quintiles(image, geometry, scale=100):
    histogram_quintile = image.reduceRegion(reducer=ee.Reducer.countDistinct(), geometry=geometry, scale=scale,  bestEffort=True, maxPixels=1e13, tileScale=2)
    return histogram_quintile

def get_wlc_stats(wlc, aoi):
    aoi_as_fc = ee.FeatureCollection(aoi)
    wlc_quintile = _quintile(wlc, aoi_as_fc)

    return wlc_quintile


def get_summary_statistics(wlc, aoi, benefits, costs, constraints):
    # returns summarys for the dashboard. 
    # restoration sutibuility
    wlc_summary = get_wlc_stats(wlc,aoi)

    # benefits
    all_benefits = get_benefit_stats(benefits, aoi)

    # costs
    all_costs = get_cost_stats(costs, aoi)

    #cconstraints
    all_constraints = get_constraint_status(constraints, aoi)

    return wlc_summary.merge(all_benefits).merge(all_costs).merge(all_constraints)

if __name__ == "__main__":
    ee.Initialize()
    io = fake_io()
    region = fake_aoi_io()
    layerlist = io.layer_list

    aoi = region.get_aoi_ee()
    wlc_io = gee_compute(region,io,io)
    wlc_out = wlc_io.wlc()
    # wlc_out = wlc_out[0]
    # get wlc quntiles  
    t1 = get_wlc_stats(wlc_out, aoi)
    print(t1.getInfo())

    # get dict of quintile counts for wlc
    # print(type(wlc_out),wlc_out.bandNames().getInfo())
    wlc_quintile, bad_features = wlc_io.quintile_normalization(wlc_out,ee.FeatureCollection(aoi))
    t2 = _count_quintiles(wlc_quintile, aoi)
    print(t2.getInfo())