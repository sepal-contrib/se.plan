import json

import ipyvuetify as v
import pandas as pd 
import numpy as np

from component import parameter as cp
from component.message import cm


class PriorityTable(v.SimpleTable):
    
    _labels = [
        cm.benefits.no_importance,
        cm.benefits.low_importance,
        cm.benefits.neutral,
        cm.benefits.important,
        cm.benefits.very_important,
    ]
            
    _colors = cp.gradient(5)
    
    _BENEFITS = pd.read_csv(cp.layer_list).fillna('')
    _BENEFITS = _BENEFITS[_BENEFITS.theme == 'benefits'].subtheme.unique()
    
    _DEFAULT_V_MODEL = {name: 0 for name in _BENEFITS}
    
    def __init__(self):
        
        
        # construct the checkbox list
        self.checkbox_list = {}
        for name in self._BENEFITS:
            line = []
            for i, color in enumerate(self._colors):
                line.append(v.Checkbox(
                    color = color, 
                    _metadata = {'label': name, 'val': i}, 
                    v_model = i==0
                ))
            self.checkbox_list[name] = line
            
        # construct the rows of the table
        rows = []
        for name in self._BENEFITS:
            row  = [v.Html(tag = 'td', children = [name])]
            for j in range(len(self._colors)):
                row.append(v.Html(tag = 'td', children = [self.checkbox_list[name][j]]))
            rows.append(v.Html(tag = 'tr', children = row))
        
        # create the table
        super().__init__(
            v_model = json.dumps(self._DEFAULT_V_MODEL),
            children = [
                v.Html(tag = 'thead', children = [
                    v.Html(tag = 'tr', children = (
                        [ v.Html(tag = 'th', children = [cm.benefits.priority])]
                        + [v.Html(tag = 'th', children = [label]) for label  in self._labels]
                    ))
                ]),
                v.Html(tag = 'tbody', children = rows)
            ]
        )
        
        # link the checks with the v_model
        for name in self._BENEFITS:
            for check in self.checkbox_list[name]:
                check.observe(self._on_check_change, 'v_model')
        
    def _on_check_change(self, change):
        
        line = change['owner']._metadata['label']
        
        # if checkbox is unique and change == false recheck 
        if change['new'] == False:
            unique = True
            for check in self.checkbox_list[line]:
                if check.v_model == True:
                    unique = False 
                    break
            
            change['owner'].v_model = unique
        
        else:
            # uncheck all the others in the line
            for check in self.checkbox_list[line]:
                if check != change['owner']:
                    check.v_model = False
            
            # change the table model 
            tmp = json.loads(self.v_model)
            tmp[line] = change['owner']._metadata['val']
            self.v_model = json.dumps(tmp)
            
        return
    
    def load_data(self, data):
        """load the data from a questionnaire io"""
        
        data = json.loads(data)
        
        # check the appropriate checkboxes 
        for k, v in data.items():
            self.checkbox_list[k][v].v_model = True
        
        return self
            