import ipyvuetify as v 
from sepal_ui import sepalwidgets as sw 
from sepal_ui.scripts import utils as su
import geopandas as gpd

from component.message import cm

class LoadShapes(v.ExpansionPanels):

    def __init__(self):

        # add a btn to click 
        self.w_btn = sw.Btn(cm.map.shapes.btn, icon='mdi-download', class_='ml-2')

        # and the file selector
        self.w_file = sw.FileInput(['.shp', '.geojson', '.gpkg', '.kml'], label=cm.map.shapes.file)

        # and the feature selection 
        self.w_feature = v.Select(
            label = cm.map.shapes.feature,
            items = None,
            v_model = None
        )
        
        self.alert = sw.Alert()

        header = v.ExpansionPanelHeader(
            disable_icon_rotate = True,
            children=[cm.map.shapes.title],
            v_slots = [{
                'name': 'actions',
                'children' : v.Icon(children=['mdi-download'])
            }]
        )

        content = v.ExpansionPanelContent(children=[self.w_file, self.w_feature, self.w_btn, self.alert])

        #create the widget 
        super().__init__(
            class_="mb-5 mt-2", 
            children=[v.ExpansionPanel(children=[header, content])]
        )
        
        # add js behaviour 
        self.w_file.observe(self._load_features, 'v_model')
        
    def _load_features(self, change):
        
        #empty the feature widget 
        self.w_feature.v_model = None 
        self.w_feature.items = None
        
        # load the features from the selected file
        df = gpd.read_file(self.w_file.v_model, ignore_geometry=True)
        
        # load the properties 
        self.w_feature.items = sorted(set(df.columns.to_list()))
        
        return self
    
    def read_data(self):
        
        if self.w_feature.v_model == None:
            self.alert.add_msg("Please select data")
            return (None, None)
        
        return gpd.read_file(self.w_file.v_model), self.w_feature.v_model
        
        