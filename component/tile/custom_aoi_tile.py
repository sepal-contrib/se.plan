from sepal_ui.aoi.tile_aoi import TileAoi
from sepal_ui.scripts import run_aoi_selection

class CustomTileAoi(TileAoi):
    
    def bind_aoi_process(self, widget, event, data):
        """
        Customize the binding process, if the aoi is out of the LMIC borders, raise an error. 
        """
        
        # lock the btn
        widget.toggle_loading()            
            
        try:
            # create the aoi asset
            run_aoi_selection.run_aoi_selection(
                output      = self.aoi_output, 
                list_method = self.SELECTION_METHOD, 
                io          = self.io,
                folder      = self.folder
            )
            
            # check if the aoi is in the LMIC
            #lmic_ee = ee.FeatureCollection('users/bornToBeAlive/lmic').geometry()
            #if not lmic_ee.contains(self.io.get_aoi_ee().geometry()):
            #    self.io.clear_attributes()
            #    raise Exception("Your AOI should be included in LMIC")
            
            # display the resulting aoi on the map
            if self.io.get_aoi_ee():
                self.m.hide_dc()
                self.io.display_on_map(self.m)
            
        except Exception as e: 
            self.aoi_output.add_live_msg(str(e), 'error') 
        
        # free the btn
        widget.toggle_loading()
    
        return self