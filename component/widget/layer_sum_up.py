import ipyvuetify as v 
import pandas as pd
from ipywidgets import Output
from matplotlib import pyplot as plt

from component import parameter as cp

class LayerFull(v.Layout):
    
    COLORS = cp.gradient(5) + ['grey']
    
    def __init__(self, layer_name, values, aoi_name):
        
        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna('')
        layer_row = layer_list[layer_list.layer_name == layer_name]
        
        if len(layer_row) != 1:
            raise IndexError(f"The layer {layer_name} is not part of the existing layers of the application. Please contact our maintainer.")
        
        # build the internal details        
        details = v.ExpansionPanels(xs12=True, class_="mt-3", children= [
            v.ExpansionPanel(children = [
                v.ExpansionPanelHeader(children=['Details'], expand_icon='mdi-help-circle-outline', disable_icon_rotate=True),
                v.ExpansionPanelContent(children=[layer_row.layer_info.values[0]])
            ])
        ])
        
        # create a title with the layer name
        title = v.Html(class_="mt-2 mb-2", xs12= True, tag="h3", children=[f'{layer_name} ({layer_row.unit.values[0]})'])
        
        # taken from https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python
        def human_format(num, round_to=2):
            magnitude = 0
            while abs(num) >= 1000:
                magnitude += 1
                num = round(num / 1000.0, round_to)
            return '{:.{}f}{}'.format(round(num, round_to), round_to, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
        
        # create a matplotlib stack horizontal bar chart 
        chart = Output()
        with chart:
            
            # change pyplot style 
            plt.style.use('dark_background')
            
            # create the chart
            fig, ax = plt.subplots(figsize=[50, len(values)*2], facecolor=((0,0,0,0)))
            
            # set the datas 
            norm_values = [v/values[0]*100 for v in reversed(values)]
            names = [f'Sub area {i}' if i else aoi_name for i in range(len(values))][::-1]
            human_values = [f"{human_format(val)}" for val in reversed(values)]
            colors = ['grey' if i else v.theme.themes.dark.primary for i in range(len(values))][::-1]
            
            # add the axes
            ax.barh(names, norm_values, color=colors)
            
            # add the text
            for i, (norm, name, val, color) in enumerate(zip(norm_values, names, human_values, colors)):
                ax.text(norm+1, i, val, fontsize=40, color=color)
            
            # cosmetic tuning
            ax.set_xlim(0, 110)
            ax.tick_params(axis='y', which='major', pad=30, labelsize=40, left=False)
            ax.tick_params(axis='x', bottom=False, labelbottom=False)
            ax.set_frame_on(False)

            #ax.set_axis_off()
            #ax.set_facecolor((0, 0, 0, 0))

            plt.show()
        
        # create the result table
        #head = [v.Html(tag='thead', children=[v.Html(tag='tr', children=[
        #    v.Html(tag='th', children = [f"value ()"]),
        #    v.Html(tag='th', children = ["ratio"])
        #])])]
        
        
        
        #rows = []
        #for val, clr in zip(values, self.COLORS):
        #    
        ##    if val != 0:
         #       row = v.Html(tag='tr', children=[
         #           v.Html(
         #               style_=f"color: {clr}",
         #               color= clr, 
         #               tag='td', 
         #               children=[f"{human_format(val)}"]
         #           ),
         #           v.Html(tag='td', children=[v.ProgressLinear(
         #               v_model=int(val/total*100), 
         #               color=clr, 
         #               background_opacity=0.1, 
         #               height=10, 
         #               rounded=True, 
         #               background_color='grey', 
         #               dense=True
         #           )])
         #       ])
         #   
         #       rows.append(row)
#
        #body = [v.Html(tag='tbody', children = rows)]
        #table = v.SimpleTable(xs12=True, children = head + body)
        
        super().__init__(
            class_ = "ma-5",
            row=True,
            children=[
                v.Flex(xs12=True, children = [title]),
                v.Flex(xs12=True, children=[chart]),
                v.Flex(xs12=True, children=[details])
            ]
        )
        
class LayerPercentage(v.Layout):
    
    def __init__(self, layer_name, pcts):
        
        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna('')
        layer_row = layer_list[layer_list.layer_name == layer_name]

        if len(layer_row) != 1 and layer_name not in cp.criterias:
            raise IndexError(f"The layer {layer_name} is not part of the existing layers of the application. Please contact our maintainer.")
        if len(layer_row) != 1 and layer_name in cp.criterias:
            layer_row = pd.DataFrame([["","",layer_name,"",layer_name,"HA"]], columns = ['theme', 'subtheme', 'layer_name', 'gee_asset', 'layer_info', 'unit'])

        #add the title
        title = v.Html(tag='h4', children=[layer_name])
        # build the internal details        
        details = v.ExpansionPanels(xs12=True, class_="mt-3", children= [
            v.ExpansionPanel(children = [
                v.ExpansionPanelHeader(children=['Details'], expand_icon='mdi-help-circle-outline', disable_icon_rotate=True),
                v.ExpansionPanelContent(children=[layer_row.layer_info.values[0]])
            ])
        ])
        
        # create the list of value
        spans = []
        for i, val in enumerate(pcts):
            if val != 0:
                spans.append(v.Html(
                    tag='span',
                    class_ = 'ml-1 mr-1',
                    style_ = f'color: {"grey" if i else v.theme.themes.dark.primary}',
                    children=[f'{round(val,2)}%']
                ))
                
        super().__init__(
            class_ = "ma-5",
            row=True, 
            children = [
                v.Flex(xs12=True, children=[title] + spans),
                v.Flex(xs12=True, children=[details])
            ]
        )
        
        
            
            
            
            
        
        