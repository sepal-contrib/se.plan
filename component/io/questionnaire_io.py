import random 
import json

from component import parameter as cp

class QuestionnaireIo():
    
    def __init__(self):
    
        self.constraints = ''
        self.priorities = ''
        
# questionnaire_io.constraints = { name of the criteria : [ bool activated, bool gt or lt, value] } for each criteria as json dict  
default_questionnaire_io = QuestionnaireIo()

criterias = {}
for name, dict_ in cp.criterias.items():
    
    val = dict_['content']
    
    if val == None: # binary criteria 
        crit = random.random() < .5
    elif isinstance(val, list):
        crit = val[int(random.random()*3)]['value']
    elif isinstance(val, int):
        crit = int(random.random() * val)
    else: # header
        continue
    
    # randomly activate them
    crit = crit if random.random() < .5 else -1
    
    # set them in the criterias list 
    criterias[name] = crit

default_questionnaire_io.constraints = json.dumps(criterias)

# questionnaire_io.priorities = { priorityName: value from 0 to 4 } for each priority as json dict
priorities = {p: random.randint(0,4) for p in cp.priorities}
default_questionnaire_io.priorities = json.dumps(priorities)