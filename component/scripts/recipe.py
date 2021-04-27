import json 
from datetime import datetime
from copy import copy

from component import parameter as cp

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
    
    
    
        
        