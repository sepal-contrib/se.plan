import numpy as np
import json
from typing import Any, Tuple
import ee
ee.Initialize()
# client side calcs
# def chapman_richards(age: float, b0: float, b1: float, b2: float):
#     return (b0 * (1 - np.exp(-b1 * age))) ** b2


# def growth_function_by_hectares(
#     growth_func, x: float, parameters: Tuple[float], hectares: float
# ):
#     return growth_func(x, *parameters) * hectares


# def get_growth_params(params, key):
#     return params[key]


# def get_growth_hectares(values, hectares, age):
#     res = growth_function_by_hectares(
#         chapman_richards, age, values["parameters"], hectares
#     )
#     return res

def carbon_growth_function(stand_age:ee.Image, paramters_stack:ee.Image):
  #// b0(1-EXP(-b2Age))^b2
  carbonHa = ee.Image(0).expression("(b0 *( 1 - exp)) ** b2",{
    'b0': paramters_stack.select('b0'),
    'exp': (stand_age.multiply(paramters_stack.select('b1').multiply(-1))).exp(),
    'b2': ee.Image(paramters_stack.select('b2'))
  }).rename('carbon');
  
  return carbonHa

def get_paired_img():
    ''' tmp function to make paired image for spatial carbon calc. replace once finalized with exported img'''
    gez = ee.FeatureCollection("projects/sig-misc-ee/assets/sbp/ecofloristic_zones")
    CONTINENTAL_REGIONS = ee.FeatureCollection("projects/sig-misc-ee/assets/sbp/continental_regions")
    gez_map = ee.Dictionary({
        #1 humid
        'Tropical rainforest':1,
        'Tropical moist deciduous forest':1,
        'Temperate oceanic forest':1,
        'Temperate continental forest':1,
        'Boreal coniferous forest':1,
        'Subtropical humid forest':1,
        #2dry
        'Temperate steppe':2,
        'Subtropical desert':2,
        'Subtropical steppe':2,
        'Tropical shrubland':2,
        'Tropical dry forest':2,
        'Tropical desert':2,
        'Subtropical dry forest':2,
        'Temperate desert':2,
        'Boreal tundra woodland':2,
        # 3/4 nd
        'Water':3,
        'No data':3,
        'Polar':3,
        'Boreal mountain system':4,
        'Tropical mountain system':4,
        'Subtropical mountain system':4,
        'Temperate mountain system':4,
    })
    continental_map = ee.Dictionary({
        'Asia':5,
        'Asia (insular)':5,
        'Indian Ocean':5,
        'Australia':5,
        'New Zealand':5,
        'Africa':4,
        'Europe':3,
        'South America':2,
        'North America':1,
        'Pacific Ocean':6,
        'Atlantic Ocean':6,
        'Antarctica':6,
        'Arctic Ocean':6,
    })
    def eePair(img1, img2):
        pairImg = ee.Image(0).expression(
            "0.5 * (a + b) * (a + b + 1) + b", {
                'a': img1,
                'b': img2
            })
        return pairImg

    gez_region_code = gez.map(lambda f: f.set('climate_code', gez_map.get(f.get('GEZ_TERM'))))
    continential_region_code = CONTINENTAL_REGIONS.map(lambda f: f.set('continential_code', continental_map.get(f.get('REGION'))))

    empt = ee.Image()
    gez_region_img = empt.paint(gez_region_code,'climate_code')
    continential_region_img = empt.paint(continential_region_code,'continential_code')
    paired = eePair(gez_region_img, continential_region_img).int()
    return paired
    
def get_spatial_carbon(paired:ee.Image, year:int, carbon_param_path:str):
    print(carbon_param_path)
    with open(carbon_param_path) as json_file:
        params = json.load(json_file)

    out = ee.Image(0)
    for k, v in params.items():
        coe1, coe2, coe3 = v['parameters']
        coe_stack = ee.Image.cat([ee.Image(coe1), ee.Image(coe2), ee.Image(coe3)]).select([0,1,2],['b0','b1','b2'])
        carbon_region_k = carbon_growth_function(ee.Image(year), coe_stack)
        out = out.where(paired.eq(v['code']), carbon_region_k)
        
    return out