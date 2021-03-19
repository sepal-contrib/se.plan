import ipyvuetify as v

from component import parameter as cp


class AreaSumUp(v.Layout):
    
    NAMES = ['restoration potential', 'surface (MHa)', 'ratio over total surface']
    COLORS = cp.gradient(5) + ['grey']
    POTENTIALS = ['Very low', 'Low', 'Medium', 'High', 'Very High', 'Unsuitable land']
    
    def __init__(self, title, surfaces=[0]*6, total_surface=100):
        
        # init the table with 6 lines of value 0
        head = [v.Html(tag='thead', children = [v.Html(tag='tr', children = [v.Html(tag='th', children = [name]) for name in self.NAMES])])]
        
        self.rows = []
        for clr, ptl, val in zip(self.COLORS, self.POTENTIALS, surfaces):
    
            row = v.Html(tag='tr', children=[
                v.Html(tag='td', children=[ptl]),
                v.Html(tag='td', children=[f'{val}']),
                v.Html(tag='td', children=[v.ProgressLinear(
                    v_model=int(val/total_surface*100), 
                    color=clr, 
                    background_opacity=0.1, 
                    height=10, 
                    rounded=True, 
                    background_color='grey', 
                    dense=True
                )])
            ])
    
            self.rows.append(row)

        body = [v.Html(tag='tbody', children = self.rows)]
        
        table = v.SimpleTable(xs12=True, children = head + body)
        
        # init the title 
        title = v.Html(xs12=True, class_='mb-2', tag="h2", children=[title])
        
        super().__init__(row=True, class_ = "ma-5", children=[
            v.Flex(xs12=True, children=[title]), 
            v.Flex(xs12=True, children=[table])
        ])