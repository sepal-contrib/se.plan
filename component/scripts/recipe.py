import json 
from datetime import datetime
from copy import copy
from pathlib import Path
import ee

from component import parameter as cp

ee.Initialize()

def save_recipe(layer_io, aoi_io, question_io):
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
            'layer_io': layer_io.__dict__,
            'question_io': question_io.__dict__
        }
        
        json.dump(data, f)
        
    return 

def load_recipe(layer_tile, aoi_tile, questionnaire_tile, path):
    """load the recipe element in the different element of the app"""
    
    # cast to pathlib
    path = Path(path)
    
    # open the file and load the ios 
    with path.open() as f:
            
        data = json.loads(f.read())
            
        # load the aoi_io
        for attr, val in data['aoi_io'].items():
            getattr(aoi_tile.io, attr) #raise an error if is not existing
            setattr(aoi_tile.io, attr, val)
                
        # if the aoi_io is an admin I need to reload the featurecollection
        if aoi_tile.io.is_admin():
                
            if aoi_tile.io.adm0:
                aoi_tile.io.feature_collection = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_CODE', aoi_tile.io.adm0))
            elif aoi_tile.io.adm1:
                aoi_tile.io.feature_collection = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM1_CODE', aoi_tile.io.adm1))
            elif aoi_tile.io.adm2:
                aoi_tile.io.feature_collection = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq('ADM2_CODE', aoi_tile.io.adm2))
                
        # validate the aoi 
        aoi_tile.aoi_select_btn.fire_event('click','')
                    
        # load the layer_io 
        for attr, val in data['layer_io'].items():
            getattr(layer_tile.io, attr)
            setattr(layer_tile.io, attr, val)
            
        # reload the layer table
        layer_tile.apply_values(layer_tile.io.layer_list)
        
        # load the questionnaire 
        for attr, val in data['question_io'].items():
            getattr(questionnaire_tile.io, attr)
            setattr(questionnaire_tile.io, attr, val)
            
        # reload the widgets
        questionnaire_tile.constraint_tile.load_data(questionnaire_tile.io.constraints)
        questionnaire_tile.priority_tile.table.load_data(questionnaire_tile.io.priorities)
        
        
            
    return
    
    
    
        
        