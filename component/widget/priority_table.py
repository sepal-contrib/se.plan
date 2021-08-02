import json

import ipyvuetify as v
import pandas as pd 
import numpy as np

from component import parameter as cp

class PriorityTable(v.SimpleTable):
    
    _labels = [
        'no importance',
        'low importance',
        'neutral',
        'important',
        'very important',
    ]
        
    _colors = cp.gradient(5)
    
    _BENEFITS = pd.read_csv(cp.layer_list).fillna('')
    _BENEFITS = _BENEFITS[_BENEFITS.theme == 'benefits']
    
    _DEFAULT_V_MODEL = {layer_id: 0 for layer_id in _BENEFITS.layer_id}
    
    def __init__(self):
        
        
        # construct the checkbox list
        self.checkbox_list = {}
        for layer_id in self._BENEFITS.layer_id:
            line = []
            for i, color in enumerate(self._colors):
                line.append(v.Checkbox(
                    color = color, 
                    _metadata = {'label': layer_id, 'val': i}, 
                    v_model = i==0
                ))
            self.checkbox_list[layer_id] = line
            
        # construct the rows of the table
        rows = []
        self.btn_list = []
        for i, layer_row in self._BENEFITS.iterrows():
            edit_btn = v.Icon(children=['mdi-pencil'], _metadata={'layer': layer_row.layer_id}) 
            self.btn_list.append(edit_btn)
            row = [v.Html(tag='td', children=[edit_btn])]
            row.append(v.Html(tag = 'td', children = [layer_row.layer_name]))
            for j in range(len(self._colors)):
                row.append(v.Html(tag = 'td', children = [self.checkbox_list[layer_row.layer_id][j]]))
            rows.append(v.Html(tag = 'tr', children = row))
        
        # create the table
        super().__init__(
            v_model = json.dumps(self._DEFAULT_V_MODEL),
            children = [
                v.Html(tag = 'thead', children = [
                    v.Html(tag = 'tr', children = (
                        [v.Html(tag='th', children=['action'])]
                        + [v.Html(tag = 'th', children = ['priority'])]
                        + [v.Html(tag = 'th', children = [label]) for label in self._labels]
                    ))
                ]),
                v.Html(tag = 'tbody', children = rows)
            ]
        )
        
        # link the checks with the v_model
        for name in self._BENEFITS.layer_id.tolist():
            for check in self.checkbox_list[name]:
                check.observe(self._on_check_change, 'v_model')
                
        # action on clicks 
        for icon in self.btn_list:
            icon.on_event('click', lambda *args: print('toto'))
        
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
            