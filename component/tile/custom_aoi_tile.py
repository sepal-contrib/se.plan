from sepal_ui import aoi
import pandas as pd
import ee 

from component import parameter as cp

ee.Initialize()

class CustomAoiTile(aoi.AoiTile):
    
    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)
        
        # bind an extra js behaviour 
        self.view.observe(self._check_lmic, 'updated')
    
    def _check_lmic(self, change):
        """Every time a new aoi is set check if it fits the LMIC country list"""
        
        # check over the lmic country number
        if self.view.model.admin:
            
            # read the country file
            country_codes = pd.read_csv(cp.country_list).GAUL
            included = (country_codes == self.view.w_admin_0.v_model).any()
        
        # check if the aoi is in the LMIC
        else:
        
            lmic_raster = ee.Image("projects/john-ee-282116/assets/fao-restoration/misc/lmic_global_1k")
            aoi_ee_geom = self.view.model.feature_collection.geometry()

            empt = ee.Image().byte()
            aoi_ee_raster = empt.paint(aoi_ee_geom,1)

            bit_test = aoi_ee_raster.add(lmic_raster).reduceRegion(
                reducer=ee.Reducer.bitwiseAnd(),
                geometry=aoi_ee_geom, 
                scale=1000,
                bestEffort=True,
                maxPixels=1e13
                )
            # test if bitwiseAnd is 2 (1 is partial coverage, 0 no coverage)
            included = ee.Algorithms.IsEqual(bit_test.getNumber('constant'), 2).getInfo()
        
        if not included:
            self.view.reset()
            raise Exception("Your AOI should be included in LMIC")
                
        return self
    
    
