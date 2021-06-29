import ipyvuetify as v 
from sepal_ui import sepalwidgets as sw 
from sepal_ui.scripts import utils as su
import geopandas as gpd

from component.message import cm

class CustomVector(sw.VectorField):
    
    def _update_file(self, change):
        """remove the select 'all feature' option as feature is used to name the AOIs"""
        
        def __init__(self, **kwargs):
            
            super().__init__(**kwargs)
            
            self.w_column.v_model = None
            self.w_column.items = None
            

        super()._update_file(change)

        # update the columns
        self.w_column.v_model = None
        self.w_column.items = self.w_column.items[1:]
        
        return self

class LoadShapes(v.ExpansionPanels):

    def __init__(self):

        # add a btn to click 
        self.btn = sw.Btn(cm.map.shapes.btn, icon='mdi-download', class_='ml-2')

        # and the vector selector
        self.w_vector = CustomVector(label=cm.map.shapes.file)
        
        self.alert = sw.Alert()

        header = v.ExpansionPanelHeader(
            disable_icon_rotate = True,
            children=[cm.map.shapes.title],
            v_slots = [{
                'name': 'actions',
                'children' : v.Icon(children=['mdi-download'])
            }]
        )

        content = v.ExpansionPanelContent(children=[self.w_vector, self.btn, self.alert])

        #create the widget 
        super().__init__(
            class_="mb-5 mt-2", 
            children=[v.ExpansionPanel(children=[header, content])]
        )
    
    @su.loading_button(debug=False)
    def read_data(self):
        
        if self.w_vector.v_model['column'] in ['ALL', None]:
            raise Exception("Please select data")
        
        gdf = gpd.read_file(self.w_vector.v_model['pathname'])
        
        # filter if necessary 
        if self.w_vector.v_model['value']:
            gdf = gdf[gdf[self.w_vector.v_model['column']] == self.w_vector.v_model['value']]
        
        
        return gdf, self.w_vector.v_model['column']
        
        