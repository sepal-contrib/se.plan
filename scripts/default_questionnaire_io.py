from .tile.questionnaire_tile import QuestionnaireIo
from . import parameter as pm
import random
import json

# questionnaire_io.constraints = { name of the criteria : [ bool activated, bool gt or lt, value] } for each criteria as json dict  
default_questionnaire_io = QuestionnaireIo()

criterias = {
    criteria : [
        random.random() < 0.5, 
        random.random() < 0.5,
        random.randint(0,100)
    ] for criteria in pm.criterias
}
default_questionnaire_io.constraints = json.dumps(criterias)

# questionnaire_io.potential = [ [names of land use that allow restration], treecover] as json list
potential = [
    [pm.land_use[i] for i in range(random.randint(1,len(pm.land_use)))],
    random.randint(0,100)
]
default_questionnaire_io.potential = json.dumps(potential)

# questionnaire_io.goals = name of the restoration goal
default_questionnaire_io.goals = pm.goals[random.randint(0, len(pm.goals)-1)]

# questionnaire_io.priorities = { priorityName: value from 0 to 4 } for each priority as json dict
priorities = {p: random.randint(0,4) for p in pm.priorities}
default_questionnaire_io.priorities = json.dumps(priorities)