import ipyvuetify as v

from component import parameter as cp


class AreaSumUp(v.Layout):
    
    NAMES = ['restoration potential', 'surface (MHa)', 'ratio over total surface']
    COLORS = cp.gradient(5) + ['grey']
    POTENTIALS = ['Very low', 'Low', 'Medium', 'High', 'Very High', 'Unsuitable land']
    
    def __init__(self, title, surface=None, total_surface=None):
        
        # init the table with 6 lines of value 0
        head = [v.Html(tag='thead', children = [v.Html(tag='tr', children = [v.Html(tag='th', children = [name]) for name in self.NAMES])])]
        
        self.rows = []
        for i, p in enumerate(self.POTENTIALS):
    
            row = v.Html(tag='tr', children=[
                v.Html(tag='td', children=[p]),
                v.Html(tag='td', class_='align-content-center', children=[v.TextField(
                    v_model=0,
                    solo = True, 
                    readonly = True,
                    xs2=True
                )]),
                v.Html(tag='td', children=[v.ProgressLinear(
                    v_model=0, 
                    color=self.COLORS[i], 
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
        
        # initialize the value if set 
        if None not in (surface, total_surface):
            print("j'ai vue")
            self.set_values(surface, total_surface)
        
        # init the title 
        title = v.Html(xs12=True, class_='mb-2', tag="h2", children=[title])
        
        super().__init__(row=True, class_ = "ma-5", children=[
            v.Flex(xs12=True, children=[title]), 
            v.Flex(xs12=True, children=[table])
        ])
        
    def set_values(self, surfaces, total_surface):
        """set the surfaces with the values given by the user"""
        
        for surface, row in zip(surfaces, self.rows):
            
            # display the value 
            row.children[1].children[0].v_model = surface
            
            # change the progress v_model
            row.children[2].children[0].v_model = int(surface/total_surface*100)
            
        return self