import ee
import json
ee.Initialize()

# Test loading from here
class gee_compute:
    def __init__(self, rp_aoi_io, rp_layers_io, rp_questionaire_io):
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

    def constraints_hight_low_bool (self,value, contratint_bool, name, layer_id):
        layer = {'theme':'constraints'}
        layer['name'] = name 
        
        if contratint_bool == True:
            layer['eeimage'] = ee.Image(layer_id).gt(value)
        elif contratint_bool == False:
            layer['eeimage'] = ee.Image(layer_id).lt(value)

    def get_layer_and_id(self, layername, constraints_layers):
        try:
            constraint_layer = next(item for item in constraints_layers if item["name"] == layername)
            layer_id = constraint_layer['layer']
            return constraint_layer, layer_id
        except TypeError:
            raise f"Layer {layername} does not exsit."

    def make_constraints(self, constraints, constraints_layers):
        landcover_constraints = []
        # Landcover specific constraints, todo: move this to paramters file..
        landcover_default_object = {'Bare land':22,'Shrub land':15,'Agricultural land':5, 'Agriculture':40,'Rangeland':1,'Grassland':1}

        
        for i in constraints:
            value = constraints[i]
            name = i
            landcover_default_keys = landcover_default_object.keys()
            if value == None or value == -1:
                continue

            # boolean masking lc
            if name in landcover_default_keys and type(value) is bool:
                constraint_layer, layer_id = self.get_layer_and_id('Current land cover', constraints_layers)
                landcover_value = landcover_default_object[name] 

                landcover_constraints = landcover_constraints.append(self.constraints_catagorical(landcover_value, value, name, layer_id))

            # restoration coverage % masking by lc
            elif name in landcover_default_keys and type(value) is int:
                constraint_layer, layer_id = self.get_layer_and_id('Current land cover', constraints_layers)
                landcover_value = landcover_default_object[name] 

                landcover_constraints = landcover_constraints.append(self.constraints_hight_low_bool(True, value, name, layer_id))

            #range constraints (rain, elevation, slope, ect)
            elif type(value) is int:
                treecoverpotential = ee.Image('projects/john-ee-282116/assets/fao-restoration/features/RestorePotential')
                threshold_max = value * 0.01
                continue
             #canpy cover masking... ask if we still plan to use this
            elif name == 'Tree cover':
                constraint_layer, layer_id = self.get_layer_and_id('Current canopy cover', constraints_layers)
                default = 'GLCF/GLS_TCC'#todo: have this checked from csv
                if layer_id == default:
                    cover_image = ee.ImageCollection('GLCF/GLS_TCC').filter(ee.Filter.equals('year', 2010)).select(['tree_canopy_cover'], ['c_tree_canopy_cover']).mosaic()
                else:
                    cover_image = ee.Image(layer_id)

                eeimage = {'eeimage':cover_image.lt(value)}
                constraint_layer.update(eeimage)

            # protected areas masking
            elif name == 'Protected areas':
                constraint_layer, layer_id = self.get_layer_and_id('Protected areas', constraints_layers)

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

    def minmax_normalization(self,eeimage,region): 
        mmvalues = eeimage.reduceRegion(
            **{'reducer': ee.Reducer.minMax(), 'geometry': region, 'scale': 10000, 'maxPixels': 1e13, 'bestEffort': True,
            'tileScale': 4})

        bandname = ee.String(eeimage.bandNames().get(0))
        keyMin = bandname.cat('_min')
        keyMax = bandname.cat('_max')

        imgMin = ee.Number(mmvalues.get(keyMin) )
        imgMax = ee.Number(mmvalues.get(keyMax) )

        return eeimage.unitScale(imgMin, imgMax).toFloat()

    def quintile_normalization(self, image, featurecollection, scale=100):
        quintile_collection = image.reduceRegions(collection=featurecollection, 
        reducer=ee.Reducer.percentile(percentiles=[20,40,60,80],outputNames=['low','lowmed','highmed','high']), 
        tileScale=2,scale=scale)
    
        #only use features that have non null quintiles  
        valid_quintiles = quintile_collection.filter(ee.Filter.notNull(['high','low','lowmed','highmed']))
        valid_quintiles_size = valid_quintiles.size()
        vaild_quintiles_list = valid_quintiles.toList(valid_quintiles_size)
        #catch regions where input region is null for user info
        invalid_regions = quintile_collection.filter(ee.Filter.notNull(['high','low','lowmed','highmed']).Not())

        def conditions(feature):
            feature = ee.Feature(feature)

            quintiles = ee.Image().byte()
            quintiles = quintiles.paint(ee.FeatureCollection(feature), 0)

            low = ee.Number(feature.get('low'))
            lowmed = ee.Number(feature.get('lowmed'))
            highmed = ee.Number(feature.get('highmed'))
            high = ee.Number(feature.get('high'))

            out = quintiles.where(image.lte(low),1).where(image.gt(low).And(image.lte(lowmed)),2) \
            .where(image.gt(lowmed).And(image.lte(highmed)),3) \
            .where(image.gt(highmed).And(image.lte(high)),4) \
            .where(image.gt(high),5)
            
            return out
    
        quintile_image = ee.ImageCollection(vaild_quintiles_list.map(conditions)).mosaic()
        return (quintile_image, invalid_regions)


    def normalize_image(self,layer, region, method='mixmax'):
        eeimage = layer['eeimage']
        if method == 'minmax': 
            eeimage = self.minmax_normalization(eeimage,region)
        elif method == 'quintile':
            region_as_featurecollection = ee.FeatureCollection(region)
            eeimage = self.quintile_normalization(eeimage,region_as_featurecollection)[0]
        layer.update({'eeimage':eeimage})

    def normalize_benefits(self,benefits_layers,method='minmax'):
        list(map(lambda i : self.normalize_image(i,self.selected_aoi, method), benefits_layers))

    def make_benefit_expression(self,benefits_layers):
        # build expression for benefits
        fdict_bene = {'f' + str(index): element['norm_weight'] for index, element in enumerate(benefits_layers)}
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
        layerlist = self.rp_layers_io.layer_list
        constraints = json.loads(self.rp_questionaire_io.constraints)
        # load layers and create eeimages
        benefits_layers = [i for i in layerlist if i['theme'] == 'benefits' and i['weight'] != 0]
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), benefits_layers))

        risks_layers = [i for i in layerlist if i['theme'] == 'risks']
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer'])}), risks_layers))

        costs_layers = [i for i in layerlist if i['theme'] == 'costs']
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), costs_layers))

        # constraint_layer, initialize with constant value 1 
        constraints_layers = [i for i in layerlist if i['theme'] == 'constraint']
        list(map(lambda i : i.update({'eeimage':ee.Image.constant(1)}), constraints_layers))
        constraints_layers = self.make_constraints(constraints, constraints_layers)
        # note: need to have check for geometry either here or before it reaches here...
        self.normalize_benefits(benefits_layers,method='quintile')
        
        #normalize benefit weights to 0 - 1 
        sum_weights =sum(i['weight'] for i in benefits_layers)
        list(map(lambda i : i.update({'norm_weight': round(i['weight' ] / sum_weights, 5) }), benefits_layers))

        exp, exp_dict = self.make_expression(benefits_layers,costs_layers,constraints_layers)
        print(exp, exp_dict)
        wlc_image = ee.Image.constant(1).expression(exp,exp_dict)
        
        # rather than clipping paint wlc to region
        wlc_out = ee.Image().float()
        wlc_out = wlc_out.paint(ee.FeatureCollection(self.selected_aoi), 0).where(wlc_image, wlc_image)
        
        return wlc_out #(wlc_out, benefits_layers, constraints_layers)


