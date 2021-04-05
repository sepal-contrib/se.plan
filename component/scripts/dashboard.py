import ee
import json

# dev
from test_gee_compute_params import *
from functions import *

def _quintile(image, featurecollection, scale=100):
    """ computes standard quintiles of an image based on an aoi. returns feature collection with quintiles as propeties """ 
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

    # should move quintile norm out of geeio at some point...along with all other utilities
    image_quin, bad_features = geeio.quintile_normalization(image,aoi_as_fc)
    quintile_frequency = count_quintiles(image_quin, aoi)

    return fc_quintile.first().set('frequency',quintile_frequency)
# def somefunction()

#     return {'layername':'itsname',"value":"pixelCount"}
def get_aoi_count(aoi, name):
    count_aoi = ee.Image.constant(1).rename(name).reduceRegion(**{
                        'reducer':ee.Reducer.count(), 
                        'geometry':aoi,
                        'scale':100,
                        'maxPixels':1e13,
                        })
    return count_aoi
def get_image_count(image, aoi, name):
    count_img = image.selfMask().rename(name).reduceRegion(**{
                    'reducer':ee.Reducer.count(), 
                    'geometry':aoi,
                    'scale':100,
                    'maxPixels':1e13,
                    })
    value = ee.Dictionary({'value':count_img.values()})
    out_dict = ee.Dictionary({name:value})
    return out_dict

def get_summary_statistics(wlcoutputs, geeio):
    # returns summarys for the dashboard. 
    # {name: values: [],
    #        total: int}
    aoi = geeio.selected_aoi
    count_aoi = get_aoi_count(aoi, 'aoi_count')

    # restoration sutibuility
    # note: benefits from wlc are in quintiles, so must remake 
    # with real image values!
    wlc, benefits, costs, constraints = wlcoutputs
    wlc_summary = get_image_stats(wlc, aoi, geeio)

    # benefits
    all_benefits_layers = [i for i in layerlist if i['theme'] == 'benefits']
    list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), all_benefits_layers))

    benefits_out = ee.Dictionary({'benefits':list(map(lambda i : get_image_count(i['eeimage'],aoi, i['name']), all_benefits_layers))})

    # costs
    all_costs = get_cost_stats(costs, aoi)

    #cconstraints
    all_constraints = get_constraint_status(constraints, aoi)

    return wlc_summary.merge(all_benefits).merge(all_costs).merge(all_constraints)

if __name__ == "__main__":
    ee.Initialize()
    io = fake_io()
    io_default = fake_default_io()
    region = fake_aoi_io()
    layerlist = io.layer_list

    aoi = region.get_aoi_ee()
    geeio = gee_compute(region,io,io_default,io)
    wlcoutputs= geeio.wlc()
    wlc_out = wlcoutputs[0]
    # get wlc quntiles  
    # t1 = get_image_stats(wlc_out, aoi, geeio)
    # print(t1.getInfo())

    # get dict of quintile counts for wlc
    # print(type(wlc_out),wlc_out.bandNames().getInfo())
    # wlc_quintile, bad_features = geeio.quintile_normalization(wlc_out,ee.FeatureCollection(aoi))
    # t2 = count_quintiles(wlc_quintile, aoi)
    # print(t2.getInfo())

    # test getting aoi count
    # count_aoi = get_aoi_count(aoi, 'aoi_count')
    # print(count_aoi.getInfo())

    a = wlcoutputs[1][0]
    print(a)

    b = get_image_count(a['eeimage'],aoi, a['name'])
    # print(b.getInfo())
    all_benefits_layers = [i for i in layerlist if i['theme'] == 'benefits']
    list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), all_benefits_layers))

    t = ee.Dictionary({'benefits':list(map(lambda i : get_image_count(i['eeimage'],aoi, i['name']), all_benefits_layers))})
    # seemingly works... worried a bout total areas all being same, but might be aoi
    print(t.getInfo())

