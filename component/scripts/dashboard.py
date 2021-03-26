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
def count_quintiles(image, geometry, scale=100):
    histogram_quintile = image.reduceRegion(reducer=ee.Reducer.frequencyHistogram(), geometry=geometry, scale=scale,  bestEffort=True, maxPixels=1e13, tileScale=2)
    return histogram_quintile

def get_image_stats(image, aoi, geeio, scale=100) :
    """ computes quntile breaks and count of pixels within input image. returns feature with quintiles and frequency count"""
    aoi_as_fc = ee.FeatureCollection(aoi)
    fc_quintile = _quintile(image, aoi_as_fc)

    image_quin, bad_features = geeio.quintile_normalization(image,aoi_as_fc)
    quintile_frequency = count_quintiles(image_quin, aoi)

    return fc_quintile.first().set('frequency',quintile_frequency)
# def somefunction()

#     return {'layername':'itsname',"value":"pixelCount"}

def get_summary_statistics(wlc, aoi, benefits, costs, constraints, geeio):
    # returns summarys for the dashboard. 
    # restoration sutibuility
    wlc_summary = get_image_stats(wlc, aoi, geeio)

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
    geeio = gee_compute(region,io,io)
    wlc_out, benefits_layers, constraints_layers = geeio.wlc()
    # wlc_out = wlc_out[0]
    # get wlc quntiles  
    t1 = get_image_stats(wlc_out, aoi, geeio)
    print(t1.getInfo())

    # get dict of quintile counts for wlc
    # print(type(wlc_out),wlc_out.bandNames().getInfo())
    # wlc_quintile, bad_features = geeio.quintile_normalization(wlc_out,ee.FeatureCollection(aoi))
    # t2 = count_quintiles(wlc_quintile, aoi)
    # print(t2.getInfo())