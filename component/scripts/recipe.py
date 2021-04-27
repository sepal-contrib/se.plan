import json 
from datetime import datetime
from copy import copy
from pathlib import Path
import ee

from component import parameter as cp

ee.Initialize()

def save_recipe(io, aoi_io):
    """save the recipe in a json file with a timestamp"""
    
    # get the result folder
    res_dir = cp.result_dir/aoi_io.get_aoi_name()
    res_dir.mkdir(exist_ok=True)
    
    # create the json file 
    now = datetime.now()
    json_file = res_dir/f'recipe_{now.strftime("%Y-%m-%d")}.json'
    
    with json_file.open('w') as f:
        
        aoi_dict = copy(aoi_io).__dict__
        aoi_dict.update(feature_collection = None) # remove feature collection as it's not serializable
        
        data = {
            'aoi_io': aoi_dict,
            'io': io.__dict__
        }
        
        json.dump(data, f)
        
    return 

def load_recipe(io, aoi_io, path):
    """load the recipe element in the different element of the app"""
    
    # cast to pathlib
    path = Path(path)
    
    # open the file and load the ios 
    with path.open() as f:
            
        data = json.loads(f.read())
            
        # load the aoi_io
        for attr, val in data['aoi_io'].items():
            getattr(aoi_io, attr) #raise an error if is not existing
            setattr(aoi_io, attr, val)
                
        # if the aoi_io is an admin I need to reload the featurecollection
        if aoi_io.is_admin():
                
            if aoi_io.adm0:
                aoi_io.feature_collection = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_CODE', aoi_io.adm0))
            elif aoi_io.adm1:
                aoi_io.feature_collection = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM1_CODE', aoi_io.adm1))
            elif aoi_io.adm2:
                aoi_io.feature_collection = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq('ADM2_CODE', aoi_io.adm2))
                    
        # load the io 
        for attr, val in data['io'].items():
            getattr(io, attr)
            setattr(io, attr, val)
            
    return
    
    
    
        
        