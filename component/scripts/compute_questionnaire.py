import json
import random

import pandas as pd

from component import parameter as cp

def compute_questionnaire(questionnaire_io):
    """use the questionnaire answers to produce a layer list of weight"""
    
    # description of the questionnaire_io inputs 
    
    # questionnaire_io.goals = name of the restoration goal
    # questionnaire_io.priorities = { priorityName: value from 0 to 4 } for each priority as json dict
    # questionnaire_io.potential = [ [names of land use that allow restration], treecover] as json list
    # questionnaire_io.constraints = { name of the criteria : [ bool activated, bool gt or lt, value] } for each criteria as json dict
    
    # at the moment we just load random weight values

    priorities = json.loads(questionnaire_io.priorities)
    constraints = json.loads(questionnaire_io.constraints)

    def assign_weights(index, row):
        layer_dict ={
                'name'   : row.layer_name,
                'theme' : row.theme,
                'subtheme' : row.subtheme,
                'unit': row.unit,
                'layer': row.gee_asset.strip(),
        }
        if row.theme == "benefits" :
            layer_dict['weight'] = priorities[layer_dict['subtheme']]
        else:
            try:
                constraint_weight = constraints[layer_dict['name']]
                if  constraint_weight == -1:
                    constraint_weight = 0
                #assign 1 to weight if its used, and 0 if not
                layer_dict['weight'] = min(max(int(constraint_weight), 0), 1)
            except:
                print(layer_dict['name']," is not in constraints questionnaire")
                layer_dict['weight'] = 0

        return layer_dict
    
    layers_values= [ assign_weights(i, row) for i, row in pd.read_csv(cp.layer_list).fillna('').iterrows() ]

    return layers_values