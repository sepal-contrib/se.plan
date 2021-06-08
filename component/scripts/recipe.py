import json 
from datetime import datetime
from copy import copy
from pathlib import Path
import ee

from component import parameter as cp

ee.Initialize()

def save_recipe(layer_model, aoi_model, question_model):
    """save the recipe in a json file with a timestamp"""
    
    # get the result folder
    res_dir = cp.result_dir/aoi_model.name
    res_dir.mkdir(exist_ok=True)
    
    # create the json file 
    now = datetime.now()
    json_file = res_dir/f'recipe_{now.strftime("%Y-%m-%d")}.json'
    
    with json_file.open('w') as f:
        
        # remove gdf and feature_collection from aoi_model 
        # it's not serializable 
        aoi_dict = copy(aoi_model).export_data()
        aoi_dict['feature_collection'] = None
        aoi_dict['gdf'] = None
        
        data = {
            'aoi_model': aoi_dict,
            'layer_model': layer_model.export_data(),
            'question_model': question_model.export_data()
        }
        
        json.dump(data, f)
        
    return 

def load_recipe(layer_tile, aoi_tile, questionnaire_tile, path):
    """load the recipe element in the different element of the app"""
    
    # cast to pathlib
    path = Path(path)
    
    # open the file and load the models 
    with path.open() as f:
            
        data = json.loads(f.read())
        
        # load the aoi_model
        aoi_tile.view.model.import_data(data['aoi_model'])
        
        # reload the aoi tile values 
        aoi_tile.btn.fire_event('click', None)
                    
        # load the layer_io
        layer_tile.model.import_data(data['layer_model'])
            
        # reload the layer table
        layer_tile.apply_values(layer_tile.model.layer_list)
        
        # load the questionnaire 
        questionnaire_tile.model.import_data(data['question_model'])
            
        # reload the widgets
        questionnaire_tile.constraint_tile.load_data(questionnaire_tile.model.constraints)
        questionnaire_tile.priority_tile.table.load_data(questionnaire_tile.model.priorities)
        
    return
    
    
    
        
        