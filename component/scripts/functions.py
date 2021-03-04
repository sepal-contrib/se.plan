import ee
import json
ee.Initialize()

# Test loading from here
class gee_compute:
    def __init__(self, rp_aoi_io, rp_layers_io, rp_questionaire_io):
        self.rp_aoi_io = rp_aoi_io
        self.selected_aoi = rp_aoi_io.get_aoi_ee()
        self.rp_layers_io = rp_layers_io
        self.rp_questionaire_io = rp_questionaire_io
    
    def constraints_catagorical(self, value,contratint_bool,name,layer_id):

        layer = {'theme':'constraints'}
        layer['name'] = name 

        if contratint_bool == True:
            layer['eeimage'] = ee.Image(layer_id).eq(value)
            return layer
        elif contratint_bool == False:
            layer['eeimage'] = ee.Image(layer_id).neq(value)
            return layer

    def constraints_hight_low_bool (self,value, contratint_bool, layer):
        if contratint_bool == True:
            layer['eeimage'] = ee.Image(layer['layer']).gt(value)
        elif contratint_bool == False:
            layer['eeimage'] = ee.Image(layer['layer']).lt(value)

    def make_constraints(self, constraints, constraints_layers):
        for i in constraints:
            value = constraints[i]
            name = i
            if value == None or value == -1:
                continue

            # Landcover specific constraints
            landcover_default_object = {'Bare land':22,'Shrub land':15,'Agricultural land':5}
            landcover_default_keys = landcover_default_object.keys()

            if name in landcover_default_keys:
                constraint_layer = next(item for item in constraints_layers if item["name"] == 'Current land cover')
                layer_id = constraint_layer['layer']
                landcover_constraints = [self.constraints_catagorical(landcover_default_object[i],True,i,layer_id) for i in landcover_default_keys]
            
            elif name == 'Tree cover':
                constraint_layer = next(item for item in constraints_layers if item["name"] == 'Current canopy cover')
                layer_id = constraint_layer['layer']

                default = 'GLCF/GLS_TCC'#todo: have this checked from csv
                if layer_id == default:
                    cover_image = ee.ImageCollection('GLCF/GLS_TCC').filter(ee.Filter.equals('year', 2010)).select(['tree_canopy_cover'], ['c_tree_canopy_cover']).mosaic()
                else:
                    cover_image = ee.Image(layer_id)

                eeimage = {'eeimage':cover_image.lt(value)}
                constraint_layer.update(eeimage)

            elif name == 'Protected areas':
                constraint_layer = next(item for item in constraints_layers if item["name"] == 'Protected areas')
                layer_id = constraint_layer['layer']
                protected_feature = ee.FeatureCollection(layer_id)
                protected_image = protected_feature.filter(ee.Filter.neq('WDPAID', {})).reduceToImage(**{
                'properties': ['WDPAID'], 'reducer': ee.Reducer.first()}).gt(0).unmask(0).rename('wdpa')
                eeimage = {'eeimage':protected_image}
                constraint_layer.update(eeimage)
            
            else:
                constraint_layer = next(item for item in constraints_layers if item["name"] == name)

                self.constraints_hight_low_bool(value,True,constraint_layer)

        constraints_layers = constraints_layers + landcover_constraints
        return constraints_layers

    def minmaxNormalization(self,eeimage,region): 
        mmvalues = eeimage.reduceRegion(
            **{'reducer': ee.Reducer.minMax(), 'geometry': region, 'scale': 10000, 'maxPixels': 1e13, 'bestEffort': True,
            'tileScale': 4})

        bandname = ee.String(eeimage.bandNames().get(0))
        keyMin = bandname.cat('_min')
        keyMax = bandname.cat('_max')

        imgMin = ee.Number(mmvalues.get(keyMin) )
        imgMax = ee.Number(mmvalues.get(keyMax) )

        return eeimage.unitScale(imgMin, imgMax).toFloat()

    def quantileGetNumbers(self,eeimage,percentiles):
        bandname = ee.String(eeimage.bandNames().get(0))
        
        low = ee.Number(percentiles.get( bandname.cat('_low')))
        lowmed = ee.Number(percentiles.get( bandname.cat('_lowmed')))
        highmed = ee.Number(percentiles.get( bandname.cat('_highmed')))
        high = ee.Number(percentiles.get( bandname.cat('_high')))
        
        return low, lowmed, highmed, high

    def quantileNormalization(self,eeimage,region):
        percentiles = eeimage.reduceRegion(**{'reducer':ee.Reducer.percentile([20,40,60,80],['low','lowmed','highmed','high']),
            'geometry':region, 'scale':100, 'bestEffort':True, 'maxPixels':1e13, 'tileScale':2})
        
        low, lowmed, highmed, high = self.quantileGetNumbers(eeimage, percentiles)

        out = eeimage.where(eeimage.lte(low),1) \
            .where(eeimage.gt(low).And(eeimage.lte(lowmed)),2) \
            .where(eeimage.gt(lowmed).And(eeimage.lte(highmed)),3) \
            .where(eeimage.gt(highmed).And(eeimage.lte(high)),4) \
            .where(eeimage.gt(high),5)
        return out

    def normalizeImage(self,layer, region, method='mixmax'):
        eeimage = layer['eeimage']
        if method == 'minmax': 
            eeimage = self.minmaxNormalization(eeimage,region)#.rename('minmzx')
        elif method == 'quantile':
            eeimage = self.quantileNormalization(eeimage,region)#.rename('quant')
        layer.update({'eeimage':eeimage})

    def normalizeBenefits(self,benefits_layers,method='minmax'):
        list(map(lambda i : self.normalizeImage(i,region, method), benefits_layers))

    def make_benefit_expression(self,benefits_layers):
        # build expression for benefits
        fdict_bene = {'f' + str(index): element['weight'] for index, element in enumerate(benefits_layers)}
        idict_bene = {'b' + str(index): element['eeimage'] for index, element in enumerate(benefits_layers)}

        exp_bene = ['(f' + str(index) + '*b' + str(index) + ')' for index, element in enumerate(benefits_layers)]
        # i_enum = {'b'+str(index): img.select(index) for index, element in enumerate(ranks)}
        benefits_exp = '+'.join(exp_bene).join(['(', ')'])

        return fdict_bene, idict_bene, benefits_exp 

    def make_cost_expression(self,costs_layers):
        idict = {'c' + str(index):element['eeimage'] for index, element in enumerate(costs_layers)}
        exp = ['(c' + str(index) + ')' for index, element in enumerate(costs_layers)]
        exp_string = '+'.join(exp).join(['(', ')'])

        return idict, exp_string

    def make_constraint_expression(self,constraints_layers):
        idict = {'cn' + str(index):element['eeimage'] for index, element in enumerate(constraints_layers)}
        exp = ['(cn' + str(index) + ')' for index, element in enumerate(constraints_layers)]
        exp_string = '*'.join(exp).join(['(', ')'])

        return idict, exp_string

    def make_expression(self,benefits_layers,costs_layers,constraints_layers):
        fdict_bene, idict_bene, benefits_exp = self.make_benefit_expression(benefits_layers)
        idict_cost, costs_exp = self.make_cost_expression(costs_layers)
        idict_cons, constraint_exp = self.make_constraint_expression(constraints_layers)

        expression_dict = {**fdict_bene, **idict_bene, **idict_cost, **idict_cons}
        expression = f"( ( {benefits_exp} / {costs_exp} ) * {constraint_exp} )"

        return expression, expression_dict

    def wlc(self):
        layerlist = self.rp_layers_io['layer_list'] 
        constraints = self.rp_questionaire_io #json.loads(rp_questionaire_io.constraints)
        # load layers and create eeimages
        benefits_layers = [i for i in layerlist if i['theme'] == 'benefits']
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer'])}), benefits_layers))

        risks_layers = [i for i in layerlist if i['theme'] == 'risks']
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer'])}), risks_layers))

        costs_layers = [i for i in layerlist if i['theme'] == 'costs']
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer'])}), costs_layers))

        # constraint_layer, initialize with constant value 1 
        constraints_layers = [i for i in layerlist if i['theme'] == 'constraints']
        list(map(lambda i : i.update({'eeimage':ee.Image(1)}), constraints_layers))
        constraints_layers = self.make_constraints(constraints, constraints_layers)

        self.normalizeBenefits(benefits_layers,method='quantile')
        #todo: benefit weighting 
        exp, exp_dict = self.make_expression(benefits_layers,costs_layers,constraints_layers)

        wlc_image = ee.Image(1).expression(exp,exp_dict)
        return wlc_image


# tests
rp_layers_io = {'layer_list':[{'name': 'Net imports of forest products', 'layer': 'projects/john-ee-282116/assets/fakecost', 'weight': 0,'theme':'benefits'},
{'name': 'Net imports of forest products', 'layer': 'projects/john-ee-282116/assets/fakecost', 'weight': 2,'theme':'benefits'},
{'name': 'Net imports of forest products', 'layer': 'projects/john-ee-282116/assets/fakecost', 'weight': 3,'theme':'benefits'},
{'name': 'Current land cover', 'layer': 'projects/john-ee-282116/assets/fakecost', 'weight': 3,'theme':'constraints'},
{'name': 'Current canopy cover', 'layer': 'GLCF/GLS_TCC', 'weight': 3,'theme':'constraints'}, 
{'name': 'Annual rainfall', 'layer': 'projects/john-ee-282116/assets/fakecost', 'weight': 3,'theme':'constraints'}, 
{'name': 'Accessibility to major cities', 'layer': 'user/myprofile/aFalseAsset', 'weight': 4,'theme':'costs'},
{'name': 'Establishment cost', 'layer': 'projects/john-ee-282116/assets/fakecost', 'weight': 4,'theme':'costs','subtheme':'subtheme1'},
{'name': 'Forest employment per ha of forest', 'layer': 'user/myprofile/aFalseAsset', 'weight': 6,'theme':'risks'},
{'name':'Protected areas','layer':'WCMC/WDPA/current/polygons','theme':'constraints'}, 
]}
constraints = {'Bare land': -1, 'Shrub land': True, 'Agricultural land': True, 'Annual rainfall': 5, 'Population': -1,
 'Elevation': -1, 'Slope': -1, 'Tree cover': -1, 'Protected area': -1, 'Opportunity cost': -1, 'Tree cover':89}
region = ee.Geometry.Polygon(
        [[[-78.48947375603689, -3.788304531206833],
          [-78.48947375603689, -6.1959483939283935],
          [-74.82004016228689, -6.1959483939283935],
          [-74.82004016228689, -3.788304531206833]]], None, False)


t = gee_compute(region,rp_layers_io,constraints)
print(t.wlc())
