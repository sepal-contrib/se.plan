from sepal_ui import aoi
import ee 

ee.Initialize()

class CustomAoiTile(aoi.AoiTile):
    
    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)
        
        # bind an extra js behaviour 
        self.view.observe(self._check_lmic, 'updated')
    
    def _check_lmic(self, change):
        """Every time a new aoi is set check if it fits the LMIC country list"""
        
        # check if the aoi is in the LMIC
        margin = 1000 # 1Km
        lmic_ee = ee.FeatureCollection('users/bornToBeAlive/lmic')
        aoi_ee_geom = self.view.model.feature_collection.geometry()
        test = lmic_ee \
            .filterBounds(aoi_ee_geom) \
            .geometry() \
            .contains(aoi_ee_geom, margin)
            
        # without .buffer(margin, margin/2) I have difficulties to get the aoi that cross borders
        # if I add it it take ages
            
        if not test.getInfo():
            self.view.reset()
            raise Exception("Your AOI should be included in LMIC")
                
        return self
    
    
