from pathlib import Path

from sepal_ui import sepalwidgets as sw 
from sepal_ui import mapping as sm
import ipyvuetify as v
from shapely import geometry as sg 
import geopandas as gpd
import geemap
import ee
import json
from ipyleaflet import WidgetControl
from ipyleaflet import GeoJSON
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex

from component.message import cm
from component import parameter as cp
from component import scripts as cs
from component import widget as cw

class MapTile(sw.Tile):
    
    def __init__(self, geeio, aoi_io, area_tile, theme_tile):
        
        # add the explanation
        mkd = sw.Markdown('  \n'.join(cm.map.txt))
        
        # create a save widget 
        self.save = cw.ExportMap()
        
        # create the map 
        self.m = sm.SepalMap(dc=True).hide_dc()
        self.m.add_control(WidgetControl(widget=self.save, position='topleft'))
        self.m.add_colorbar(colors=cp.red_to_green, vmin=0, vmax=5)
        
        # drawing managment
        self.draw_features = {'type': 'FeatureCollection', 'features': []}
        self.colors = []
        
        # create a layout with 2 btn 
        self.map_btn = sw.Btn(cm.compute.btn, class_='ma-2')
        self.compute_dashboard = sw.Btn(cm.map.compute_dashboard, class_= 'ma-2')
        
        # ios
        self.geeio = geeio
        self.aoi_io = aoi_io
        
        # get the dashboard tile 
        self.area_tile = area_tile
        self.theme_tile = theme_tile
        
        #init the final layers 
        self.final_layer = None
        self.area_dashboard = None
        self.theme_dashboard = None
        
        # create the tile
        super().__init__(
            id_ = "map_widget",
            title = cm.map.title,
            inputs = [mkd, self.m],
            output = sw.Alert(),
            btn = v.Layout(children=[
                self.map_btn, 
                self.compute_dashboard,
                #self.to_asset, 
                #self.to_sepal,
            ])
        )
        
        # add js behaviour 
        self.compute_dashboard.on_event('click', self._dashboard)
        self.m.dc.on_draw(self._handle_draw)
        self.map_btn.on_event('click', self._compute)
        
    def _compute(self, widget, data, event):
        """compute the restoration plan and display the map"""
    
        widget.toggle_loading()
    
        try: 
        
            # create a layer and a dashboard 
            self.final_layer = self.geeio.wlc()
            
            # display the layer in the map
            cs.display_layer(self.final_layer, self.aoi_io, self.m)
            self.save.set_data(self.final_layer, self.aoi_io.get_aoi_ee().geometry())
        
            # add the possiblity to draw on the map and release the compute dashboard btn
            self.m.show_dc()
        
        except Exception as e:
            self.output.add_msg(f'{e}', 'error')
            
        widget.toggle_loading()
        
        return self
    
    def _save_features(self):
        """save the features as layers on the map"""
        
        # remove any sub aoi layer
        [self.m.remove_layer(l) for l in self.m.layers if "sub aoi" in l.name]
        
        # save the drawn features 
        draw_features = self.draw_features 
        
        # remove the shapes from the dc 
        # as a side effect the draw_feature member will be emptied
        self.m.dc.clear()
        
        # reset the draw_features 
        self.draw_features = draw_features
        
        # set up the colors using the tab10 matplotlib colormap
        self.colors = [to_hex(plt.cm.tab10(i)) for i in range(len(self.draw_features['features']))]
        
        # create a layer for each aoi 
        for i, (feat, color) in enumerate(zip(self.draw_features['features'], self.colors)):
            style = {**cp.aoi_style, 'color': color, 'fillColor': color}
            layer = GeoJSON(data=feat, style=style, name = f'sub aoi {i}')
            self.m.add_layer(layer)
            
        return self
    
    def _dashboard(self, widget, data, event):
        
        widget.toggle_loading()
        
        # handle the drawing features, affect them with a color an display them on the map as layers
        self._save_features()

        # retreive the area and theme json result
        self.area_dashboard, self.theme_dashboard = cs.get_stats(
            self.geeio,
            self.aoi_io,
            self.draw_features
        )
        
        self.theme_tile.dev_set_summary(self.theme_dashboard, self.aoi_io.get_aoi_name(), self.colors)
        self.area_tile.set_summary(self.area_dashboard)
        
        widget.toggle_loading()
        
        return self
        
    def _handle_draw(self, target, action, geo_json):
        """handle the draw on map event"""
        
        # polygonize circles 
        if 'radius' in geo_json['properties']['style']:
            geo_json = self.polygonize(geo_json)
        
        if action == 'created': # no edit as you don't know which one to change
            self.draw_features['features'].append(geo_json)
        elif action == 'deleted':
            self.draw_features['features'].remove(geo_json)
            
        return self
    
    @staticmethod
    def polygonize(geo_json):
        """
        Transform a ipyleaflet circle (a point with a radius) into a GeoJson multipolygon
        
        Params:
            geo_json (json): the circle geojson
            
        Return:
            (json): the polygonised circle
        """
        
        # get the input
        radius = geo_json['properties']['style']['radius']
        coordinates = geo_json['geometry']['coordinates']
        
        # create shapely point 
        circle = gpd.GeoSeries([sg.Point(coordinates)], crs=4326).to_crs(3857).buffer(radius).to_crs(4326)
        
        # insert it in the geo_json 
        json = geo_json
        json['geometry'] = circle[0].__geo_interface__
        
        return json