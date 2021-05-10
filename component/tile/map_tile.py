from sepal_ui import sepalwidgets as sw 
from sepal_ui import mapping as sm
import ipyvuetify as v
from shapely import geometry as sg 
import geopandas as gpd
import geemap
import ee
import json

from component.message import cm
from component import parameter as cp
from component import scripts as cs

class MapTile(sw.Tile):
    
    def __init__(self, geeio, aoi_io, area_tile, theme_tile):
        
        # add the explanation
        mkd = sw.Markdown('  \n'.join(cm.map.txt))
        
        # create the map 
        self.m = sm.SepalMap(dc=True).hide_dc()
        self.m.add_colorbar(colors=cp.red_to_green, vmin=0, vmax=5)
        
        # drawing managment
        self.draw_features = {'type': 'FeatureCollection', 'features': []}
        
        # create a layout with 2 btn 
        self.map_btn = sw.Btn(cm.compute.btn, class_='ma-2', disabled=True)
        self.compute_dashboard = sw.Btn(cm.map.compute_dashboard, class_= 'ma-2', disabled=False)
        self.to_asset = sw.Btn(cm.map.to_asset, class_='ma-2', disabled=True)
        self.to_sepal = sw.Btn(cm.map.to_sepal, class_='ma-2', disabled=True)
        

        # ios
        self.geeio = geeio
        self.aoi_io = aoi_io
        
        # get the dashboard tile 
        self.area_tile = area_tile
        self.theme_tile = theme_tile
        # create the tile
        super().__init__(
            id_ = "map_widget",
            title = cm.map.title,
            inputs = [mkd, self.m],
            output = sw.Alert(),
            btn = v.Layout(children=[
                self.map_btn, 
                self.compute_dashboard,
                self.to_asset, 
                self.to_sepal,
            ])
        )
        
        # add js behaviour 
        self.compute_dashboard.on_event('click', self._dashboard)
        self.m.dc.on_draw(self.handle_draw)
        
    def _compute(self, widget, data, event):
        """compute the restoration plan and display both the maps and the dashboard content"""
    
        widget.toggle_loading()
    
        # create a layer and a dashboard 
        layer = self.geeio.wlc()
        # setattr(self, geeio, geeio)
        # display the layer in the map
        # layer = wlcoutputs[0]
        cs.display_layer(layer, self.aoi_io, self.m)
        
        # add the possiblity to draw on the map and release the compute dashboard btn
        self.m.show_dc()
        
        # display the dashboard 
        # self.area_tile.set_summary(dashboard) # calling it without argument will lead to fake output
        # self.theme_tile.dev_set_summary(dashboard) # calling it without argument will lead to fake output
    
        widget.toggle_loading()
        
        return self
    
    def _dashboard(self, widget, data, event):
        
        widget.toggle_loading()
        
        final_dashboard = sw.Markdown("**No dashboarding function yet**")
        
        selected_info = self.aoi_io.get_not_null_attrs()
        
        final_layer = self.m.ee_layer_dict['restoration layer']['ee_object']
        
        # convert the drawn features to ee.FeatureCollection 
        ee_feature_collection = geemap.geojson_to_ee(self.draw_features)

        wlcoutputs = self.geeio.wlcoutputs
#         dev local path
        DOWNLOADPATH = r'/home/jdilger//'
        if len(self.draw_features['features']) > 0:
            # compute stats for sub aois
            featurecol_dashboard = cs.get_stats_w_sub_aoi(wlcoutputs, self.geeio, selected_info, self.draw_features)

            # export sub aoi stats
            # cs.export_stats(featurecol_dashboard)
            # grab csv 
            
        else:
            featurecol_dashboard = cs.get_stats_as_feature_collection(wlcoutputs, self.geeio, selected_info)
            exportname = cs.export_stats(featurecol_dashboard)
            cs.gee.wait_for_completion(exportname, self.output)
            # grab json
            gdrive = cs.gdrive()
            file = gdrive.get_files(f'{exportname}.geojson')
            gdrive.download_files(file,DOWNLOADPATH)
        
        
        with open(f"{DOWNLOADPATH}{file[0]['name']}",'r') as f:
            json_results = json.load(f)
    
        self.theme_tile.dev_set_summary(json_results)
        self.area_tile.set_summary(json_results)
        
        self.output.add_live_msg('Downloaded to Sepal', 'success')
        
        widget.toggle_loading()
        return self

    def handle_draw(self, target, action, geo_json):

        geom = geemap.geojson_to_ee(geo_json, False)
        feature = ee.Feature(geom)
        
        if action == "deleted" and len(self.m.draw_features) > 0:
            self.m.draw_features.remove(feature)
        else:
            self.m.draw_features.append(feature)

        collection = ee.FeatureCollection(self.m.draw_features)
        self.m.draw_collection = collection
        
        
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