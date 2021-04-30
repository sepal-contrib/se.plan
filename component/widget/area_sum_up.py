import ipyvuetify as v
from ipywidgets import Output
from matplotlib import pyplot as plt

from component import parameter as cp
from component.message import cm


class AreaSumUp(v.Layout):
    
    NAMES = ['restoration potential', 'surface (MHa)', 'ratio over total surface (%)']
    COLORS = cp.gradient(5) + ['grey']
    POTENTIALS = ['Very low', 'Low', 'Medium', 'High', 'Very High', 'Unsuitable land']
    
    def __init__(self, title, surfaces=[0]*6):
        
        # get the total surface for ratio
        total_surface = sum(surfaces)
        
        # create a matplotlib stack horizontal bar chart 
        chart = Output()
        with chart:
            
            # create the chart
            fig, ax = plt.subplots(figsize=[50, 2])
            
            # add the axis
            for i, surface in enumerate(surfaces):
                ax.barh(title, surface, left=sum(surfaces[:i]), color=self.COLORS[i])
            
            # cosmetic tuning
            ax.set_axis_off()

            plt.show()
        
        # init the table with 6 lines of value 0
        head = [v.Html(tag='thead', children = [v.Html(tag='tr', children = [v.Html(tag='th', children = [name]) for name in self.NAMES])])]
        
        self.rows = []
        for clr, ptl, val in zip(self.COLORS, self.POTENTIALS, surfaces):
    
            row = v.Html(tag='tr', children=[
                v.Html(tag='td', children=[ptl], style_=f"color: {clr}",),
                v.Html(tag='td', children=[f'{float(val):.1f}']),
                v.Html(tag='td', children=[f'{float(val/sum(surfaces)):.1f}'])
            ])
    
            self.rows.append(row)

        body = [v.Html(tag='tbody', children = self.rows)]
        table = v.SimpleTable(small=True, xs12=True, children = head + body)
        
        # the table should not be displayed by default but as a detail expansion panel 
        ep = v.ExpansionPanels(children=[v.ExpansionPanel(children=[
            v.ExpansionPanelHeader(children=[cm.dashboard.region.detail]),
            v.ExpansionPanelContent(children=[table])
        ])])
        
        # init the title 
        title = v.Html(xs12=True, class_='mb-2', tag="h2", children=[title])
        
        super().__init__(row=True, class_ = "ma-5", children=[
            v.Flex(xs12=True, children=[title]), 
            v.Flex(xs12=True, children=[chart]),
            v.Flex(xs12=True, children=[ep])
        ])