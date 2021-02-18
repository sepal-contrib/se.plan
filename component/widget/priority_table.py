class PriorityTable(v.SimpleTable):
    
    _labels = [
        'no importance',
        'low importance',
        'neutral',
        'important',
        'very important',
    ]
        
    _colors = [
        'red',
        'orange',
        'yellow accent-3',
        'light-green',
        'green'
    ]
    
    _DEFAULT_V_MODEL = {name: 0 for name in pm.priorities}
    
    def __init__(self):
        
        
        # construct the checkbox list
        self.checkbox_list = {}
        for name in pm.priorities:
            line = []
            for i, color in enumerate(self._colors):
                line.append(v.CheckBox(
                    color = color, 
                    _metadata = {'label': name, 'val': i}, 
                    v_model = i==0
                ))
            self.checkbox_list[name] = line
            
        # construct the rows of the table
        rows = []
        for name in pm.priorities:
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
                        [ v.Html(tag = 'th', children = ['priority'])]
                        + [v.Html(tag = 'th', children = [label]) for label in self._labels]
                    ))
                ]),
                v.Html(tag = 'tbody', children = rows)
            ]
        )
        
        # link the checks with the v_model
        for name in pm.priorities:
            for check in self.checkbox_list[name]:
                check.observe(self._on_check_change, 'v_model')
        
    def _on_check_change(self, change):
        
        line = change['owner']._metadata['label']
        
        # if checkbox is unique and chang == false recheck 
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
            