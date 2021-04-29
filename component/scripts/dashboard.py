import ee
import json
import datetime
# from component import utils
import os

def _quintile(image, geometry, scale=100):
    """ computes standard quintiles of an image based on an aoi. returns feature collection with quintiles as propeties """ 
    quintile_collection = image.reduceRegion(geometry=geometry, 
                        reducer=ee.Reducer.percentile(percentiles=[20,40,60,80],outputNames=['low','lowmed','highmed','high']), 
                        tileScale=2,
                        scale=scale, 
                        maxPixels=1e13)

    return quintile_collection

def count_quintiles(image, geometry, scale=100):
    histogram_quintile = image.reduceRegion(reducer=ee.Reducer.frequencyHistogram().unweighted(),
                        geometry=geometry,
                        scale=scale, 
                        # bestEffort=True, 
                        maxPixels=1e13, 
                        tileScale=2)
    return histogram_quintile

def get_aoi_name(selected_info):
    if 'country_code' in selected_info:
        selected_name = selected_info['country_code']
    elif isinstance(selected_info,str):
        selected_name = selected_info
    else:
        # TODO : add this to lang.json 
        selected_name = 'Custom Area of Interest'
    return selected_name

def get_image_stats(image, geeio, selected_info, mask, total, scale=100, **kwargs) :
    """ computes quntile breaks and count of pixels within input image. returns feature with quintiles and frequency count"""
    # check if aoi other than whole area is being summarized.
    if 'aoi' in kwargs:
        aoi = kwargs['aoi']
    else:
        aoi = geeio.selected_aoi
    
    aoi_as_fc = ee.FeatureCollection(geeio.selected_aoi)

    # should move quintile norm out of geeio at some point...along with all other utilities
    image_quin, bad_features = geeio.quintile_normalization(image,aoi_as_fc)
    image_quin = image_quin.where(mask.eq(0),6)
    quintile_frequency = count_quintiles(image_quin, aoi)

    selected_name = get_aoi_name(selected_info)
    list_values = ee.Dictionary(quintile_frequency.values().get(0)).values()

    out_dict = ee.Dictionary({'suitibility':{
        selected_name :{'values':list_values,
        'total' : total}
        }})
    return out_dict

def get_aoi_count(aoi, name):
    count_aoi = ee.Image.constant(1).rename(name).reduceRegion(**{
                        'reducer':ee.Reducer.count(), 
                        'geometry':aoi,
                        'scale':100,
                        'maxPixels':1e13,
                        })
    return count_aoi
def get_image_percent_cover(image, aoi, name):
    """ computes the percent coverage of a constraint in relation to the total aoi. returns dict name:{value:[],total:[]}"""
    count_img = image.Not().selfMask().reduceRegion(**{
                    'reducer':ee.Reducer.count(), 
                    'geometry':aoi,
                    'scale':100,
                    'maxPixels':1e13,
                    })
    total_img = image.reduceRegion(**{
                    'reducer':ee.Reducer.count(), 
                    'geometry':aoi,
                    'scale':100,
                    'maxPixels':1e13,
                    })
    total_val = ee.Number(total_img.values().get(0))
    count_val = ee.Number(count_img.values().get(0))

    percent = count_val.divide(total_val).multiply(100)
    value = ee.Dictionary({'values':[percent],
                            'total':[total_val]})
    out_dict = ee.Dictionary({name:value})
    return out_dict
    
def get_image_sum(image, aoi, name, mask):
    """ computes the sum of image values not masked by constraints in relation to the total aoi. returns dict name:{value:[],total:[]}"""
     
    sum_img = image.updateMask(mask).reduceRegion(**{
                    'reducer':ee.Reducer.sum(), 
                    'geometry':aoi,
                    'scale':100,
                    'maxPixels':1e13,
                    })
    total_img = image.reduceRegion(**{
                    'reducer':ee.Reducer.sum(), 
                    'geometry':aoi,
                    'scale':100,
                    'maxPixels':1e13,
                    })

    value = ee.Dictionary({'values':sum_img.values(),
                            'total':total_img.values()})
    out_dict = ee.Dictionary({name:value})
    return out_dict

def get_summary_statistics(wlcoutputs, aoi, geeio, selected_info):
    # returns summarys for the dashboard. 
    # {name: values: [],
    #        total: int}
    # aoi = geeio.selected_aoi
    count_aoi = get_aoi_count(aoi, 'aoi_count')

    # restoration sutibuility
    wlc, benefits, constraints, costs = wlcoutputs
    mask = ee.ImageCollection(list(map(lambda i : ee.Image(i['eeimage']).rename('c').byte(), constraints))).min()

    # restoration pot. stats
    wlc_summary = get_image_stats(wlc, geeio, selected_info, mask, count_aoi.values().get(0))

    try:
        layer_list = geeio.rp_layers_io.layer_list
    except:
        layer_list = layerlist

    # benefits
    # remake benefits from layerlist as original output are in quintiles
    all_benefits_layers = [i for i in layer_list if i['theme'] == 'benefits']
    list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), all_benefits_layers))

    benefits_out = ee.Dictionary({'benefits':list(map(lambda i : get_image_sum(i['eeimage'],aoi, i['name'], mask), all_benefits_layers))})

    # costs
    costs_out = ee.Dictionary({'costs':list(map(lambda i : get_image_sum(i['eeimage'],aoi, i['name'], mask), costs))})

    #constraints
    constraints_out =ee.Dictionary({'constraints':list(map(lambda i : get_image_percent_cover(i['eeimage'],aoi, i['name']), constraints))}) 

    return wlc_summary.combine(benefits_out).combine(costs_out).combine(constraints_out)


def get_stats_as_feature_collection(wlcoutputs, geeio, selected_info,**kwargs):
    if 'aoi' in kwargs:
        aoi = kwargs['aoi']
    else:
        aoi = geeio.selected_aoi
    
    stats = get_summary_statistics(wlcoutputs, aoi, geeio, selected_info)
    geom = ee.Geometry.Point([0,0])
    feat = ee.Feature(geom).set(stats)
    fc = ee.FeatureCollection(feat)

    return fc

def get_stats_w_sub_aoi(wlcoutputs, geeio, selected_info, m):
    aoi_stats = get_stats_as_feature_collection(wlcoutputs, geeio, selected_info)
    sub_stats = [get_stats_as_feature_collection(wlcoutputs, geeio, f'Sub region {m.draw_features.index(i)}',aoi=i.geometry()) for i in m.draw_features]
    sub_stats = ee.FeatureCollection(sub_stats).flatten()
    combined = aoi_stats.merge(sub_stats)
    return combined

def export_stats(fc):
    now = datetime.datetime.utcnow()
    suffix = now.strftime("%Y%m%d%H%M%S")
    desc = f"restoration_dashboard_{suffix}"
    task = ee.batch.Export.table.toDrive(collection=fc, 
                                     description=desc,
                                     folder='restoration_dashboard',
                                     fileFormat='GeoJSON'
                                    )
    task.start()
    # utils.gee.wait_for_completion(desc,"")
    print(task.status())

def getdownloadasurl(fc):
    # hacky way to download data until I can figure out downlading from drive
    now = datetime.datetime.utcnow()
    suffix = now.strftime("%Y%m%d%H%M%S")
    desc = f"restoration_dashboard_{suffix}"
    url = fc.getDownloadURL('GeoJSON', filename=desc)
    dest = r"."
    file = f'{dest}/{desc}.GEOjson'

    os.system(f'curl {url} -H "Accept: application/json" -H "Content-Type: application/json" -o {file}')

    with open(file) as f:
        json_features = json.load(f)
    os.remove(file)
    return json_features

if __name__ == "__main__":
    # dev
    from test_gee_compute_params import *
    from functions import *
    ee.Initialize()
    io = fake_io()
    io_default = fake_default_io()
    region = fake_aoi_io()
    layerlist = io.layer_list

    aoi = region.get_aoi_ee()
    geeio = gee_compute(region,io,io_default,io)
    wlcoutputs= geeio.wlc()
    wlc_out = wlcoutputs[0]
    selected_info = [None]
    # test getting as fc for export
    t7 = get_stats_as_feature_collection(wlcoutputs,geeio,selected_info)
    # print(t7.getInfo())
    f = getdownloadasurl(t7)
    print(f, type(f))

    # test wrapper
    # t0 = get_summary_statistics(wlcoutputs,geeio)
    # print(t0.getInfo())
    # get wlc quntiles  
    # t1 = get_image_stats(wlc_out, geeio, selected_info)
    # print(t1.getInfo())

    # get dict of quintile counts for wlc
    # print(type(wlc_out),wlc_out.bandNames().getInfo())
    # wlc_quintile, bad_features = geeio.quintile_normalization(wlc_out,ee.FeatureCollection(aoi))
    # t2 = count_quintiles(wlc_quintile, aoi)
    # print(ee.Dictionary(t2.get('constant')).values().getInfo())

    # test getting aoi count
    # count_aoi = get_aoi_count(aoi, 'aoi_count')
    # print(count_aoi.values().getInfo())
    
    # c = wlcoutputs[2]
    # # print(c)
    # cimg = ee.ImageCollection(list(map(lambda i : ee.Image(i['eeimage']).byte(), c))).min()
    # # print(cimg)

    # a = wlcoutputs[1][0]
    # # print(a)

    # # b = get_image_count(a['eeimage'],aoi, a['name'])
    # # # print(b.getInfo())
    # all_benefits_layers = [i for i in layerlist if i['theme'] == 'benefits']
    # list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), all_benefits_layers))

    # t = ee.Dictionary({'benefits':list(map(lambda i : get_image_sum(i['eeimage'],aoi, i['name'], cimg), all_benefits_layers))})
    # # # seemingly works... worried a bout total areas all being same, but might be aoi
    # print(t.getInfo())