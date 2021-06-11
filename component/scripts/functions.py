import ee
import json

from component import parameter as cp 
from component import model

ee.Initialize()

class gee_compute:
    
    def __init__(self, rp_aoi_model, rp_layers_model, rp_questionaire_model):
        
        self.aoi_model = rp_aoi_model
        self.rp_layers_model = rp_layers_model
        self.rp_questionaire_model = rp_questionaire_model
        self.rp_default_layer = model.CustomizeLayerModel().layer_list

        # results
        self.wlcoutputs = None

        self.landcover_default_object = {
            'Bare land':60,
            'Shrub land':20,
            'Agricultural land':40, 
            'Agriculture':40,
            'Rangeland':40,
            'Grassland':30, 
            'Settlements':50
        }
    
    def constraints_catagorical(self, cat_value,contratint_bool,name,layer_id):
        '''builds and updates categorical constraints. assumes landcover  follows the copernicus landcover product schema.

        Args:
            cat_value ([int]): the value associated with a land cover class
            contratint_bool ([bool]): true the land cover is not equal to a value, false the land cover value is equal 
            name ([string]): a name to associate with the layer to build
            layer_id ([string]): 

        Returns:
            dict: returns layer dictionary with eeimage
            {name:str,
            theme:str.
            eeimage: earthengine image object}
                
        '''
      
        layer = {'theme':'constraints'}
        layer['name'] = name 
        image = ee.Image(layer_id)

        if layer_id == 'COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019':
            image = image.select("discrete_classification")
        if contratint_bool:
            layer['eeimage'] = image.neq(cat_value)
        else:
            layer['eeimage'] = image.eq(cat_value)

        return layer

    def constraints_hight_low_bool(self,value, contratint_bool, name, layer_id):

        layer = {'theme':'constraints'}
        layer['name'] = name 
        
        if contratint_bool:
            layer['eeimage'] = ee.Image(layer_id).gt(value)
        else:
            layer['eeimage'] = ee.Image(layer_id).lt(value)

    def constraints_tree_cover(self, cat_value, value, name, layer_id):
        
        layer = {'theme':'constraints'}
        layer['name'] = name 
        image = ee.Image(layer_id)

        if layer_id == 'COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019':
            image = image.select("discrete_classification")

        treecoverpotential = ee.Image('projects/john-ee-282116/assets/fao-restoration/features/RestorePotential')
        threshold_max = value * 0.01

        layer['eeimage'] = ee.Image.constant(1).where(image.eq(cat_value).And(treecoverpotential.gt(threshold_max)), 0)
        return layer

    def get_layer_and_id(self, layername, constraints_layers):
        '''Gets the layer name and dictionary. Handels cases when the layer name is a land cover constraint and not a constraint layer.

        Args:
            layername (str): the layer name
            constraints_layers (list[dict]]): The list of constaints

        Raises:
            Exception: A layer does not exist 

        Returns:
            dict, str: Dictionary of named layer, layer name
        '''
        
        try:
            if layername in  self.landcover_default_object.keys():
                constraint_layer = next(item for item in constraints_layers if item["name"] == 'Current land cover')
            else:
                constraint_layer = next(item for item in constraints_layers if item["name"] == layername)
            
            layer_id = constraint_layer['layer']
            
        except:
            raise Exception(f"Layer {layername} does not exsit.")
            
        return constraint_layer, layer_id
    
    def is_default_layer(self, name, layer_id):
        
        default_layer_id = next(item['layer'] for item in self.rp_default_layer if item["name"] == name)
        
        return layer_id == default_layer_id


    def update_range_constraint(self, value, name, constraints_layers):
        '''Updates the constraint layer with images for ranged values. 

        Args:
            value (int): The values to to mask gt/lt from GUI params
            name (str): The layer name
            constraints_layers (list[dict]]):  List of constraints

        Raises:
            RuntimeError: Errors if a layer does not have a locigal opperator in the layer_list
        '''
        
        constraint_layer, layer_id = self.get_layer_and_id(name, constraints_layers)
        
        # apply any preprocessing 
        #TODO : export images with 100 multiplication factor....
        if name == 'Slope' and self.is_default_layer(name, layer_id):
            image = ee.Image(layer_id)
            image = ee.Algorithms.Terrain(image).select('slope')
        elif name == 'Deforestation rate' and self.is_default_layer(name, layer_id):
            image = ee.Image(layer_id).multiply(1000)
        elif name == 'Natural regeneration probability' and self.is_default_layer(name, layer_id):
            image = ee.Image(layer_id).multiply(100)
        elif name == 'Property rights protection' and self.is_default_layer(name, layer_id):
            image = ee.Image(layer_id).multiply(100)
        else:
            image = ee.Image(layer_id)
        
        if constraint_layer['operator'] == 'gt':
            eeimage = {'eeimage': image.gt(value)}
        elif constraint_layer['operator'] == 'lt':
            eeimage = {'eeimage': image.lt(value)}
        else:
            raise RuntimeError(f"The layer {name} does not have a logical operator assigned. Please contact our maintainer.")
        constraint_layer.update(eeimage)

    def make_constraints(self, constraints, constraints_layers):
        '''Makes the constraints images according to answers from the constraints questionare. Constraints are handeled either as a bool, range, or percent cover of land use. Adds background geographic constraint (where restoration potential is greater than current cover, and is urban).

        Args:
            constraints (dict): constraints selected from questionare
            constraints_layers (list[dict]):  List of constraints

        Returns:
            list[dict]:  List of constraints with their ee images
        '''
        landcover_constraints = []
        default_range_constraints = [i for i in cp.criterias if type(cp.criterias[i]['content']) is list]

        for i in constraints:
            value = constraints[i]
            name = i
            
            if value == None or value == -1 : continue 
                
            try:
                constraint_layer, layer_id = self.get_layer_and_id(name, constraints_layers)
            except:
                print(name,value)
                continue
                
            # boolean masking lc
            if name in self.landcover_default_object.keys() and type(value) is bool:
                landcover_value = self.landcover_default_object[name] 
                landcover_constraints.append(self.constraints_catagorical(landcover_value, value, name, layer_id))

            # restoration coverage % masking by lc
            elif name in self.landcover_default_object.keys() and type(value) is int:
                landcover_value = self.landcover_default_object[name] 
                landcover_constraints.append(self.constraints_tree_cover(landcover_value, value, name, layer_id))

            # high med lowe constraints (rain, elevation, slope, ect)
            elif name in default_range_constraints:
                self.update_range_constraint(value, name, constraints_layers)

            # protected areas masking
            # TODO : export this and remove 
            elif name == 'Protected areas' and self.is_default_layer(name, layer_id):
                protected_feature = ee.FeatureCollection(layer_id)
                protected_image = protected_feature \
                    .filter(ee.Filter.neq('WDPAID', {})) \
                    .reduceToImage(properties = ['WDPAID'], reducer = ee.Reducer.first()) \
                    .gt(0) \
                    .unmask(0) \
                    .rename('wdpa')
                eeimage = {'eeimage':protected_image}
                constraint_layer.update(eeimage)

            # TODO : export and remove
            elif name == 'Declining population' and self.is_default_layer(name,layer_id):
                # Loctions w declining pop is 1,2 in not declining - binary 
                eeimage = {'eeimage':ee.Image(layer_id).eq(1)}
                constraint_layer.update(eeimage)
            
            else:
                # asummes 0 is constraint, 1 is keep
                eeimage = {'eeimage' : ee.Image(layer_id)}
                constraint_layer.update(eeimage)

        default_geographic = next(item for item in constraints_layers if item["name"] == 'Current tree cover less than potential')
        default_geographic.update({'eeimage' : ee.Image(default_geographic['layer'])})

        constraints_layers = constraints_layers + landcover_constraints + [default_geographic]
        
        return constraints_layers

    def minmax_normalization(self,eeimage,region,scale = 10000): 
        
        mmvalues = eeimage.reduceRegion(
            reducer = ee.Reducer.minMax(),
            geometry = region, 
            scale = scale, 
            maxPixels = 1e13,
            bestEffort = True,
            tileScale = 4
        )

        bandname = ee.String(eeimage.bandNames().get(0))
        keyMin = bandname.cat('_min')
        keyMax = bandname.cat('_max')

        imgMin = ee.Number(mmvalues.get(keyMin) )
        imgMax = ee.Number(mmvalues.get(keyMax) )

        return eeimage.unitScale(imgMin, imgMax).toFloat()

    def percentile_normalization(self, eeimage, region, scale):
        '''Calculates the 3rd and 97th percentiles of input image to rescale to 0 - 1. 

        Args:
            eeimage (ee.Image): Image to scale
            region (ee.Geometry): The region to calculate percentiles
            scale (int): scale to calculate percentiles

        Returns:
            ee.Image: Image rescaled by the 3rd and 97th percentiles
        '''
        # todo: make this more dynamic with dictionary regex. using quick fix for now

        eeimagetmp = eeimage.rename("img")
        percents = eeimagetmp.reduceRegion(geometry=region, 
            reducer=ee.Reducer.percentile(percentiles=[3,97]), 
            scale=scale)
        
        img_low = ee.Number(percents.get('img_p3') )
        img_high = ee.Number(percents.get('img_p97') ).add(0.1e-13)
        
        return  eeimage.unitScale(img_low,img_high).clamp(0, 1)

    def quintile_normalization(self, image, featurecollection, scale=100):
        '''Calculates a standard quintile normalization (20,40,60,80) for each region in a feature collection and combines into a single image.

        Args:
            image (ee.Image): The image to calculate quintiles of
            featurecollection (ee.FeatureCollection): FeatureCollection of 1 or more features 
            scale (int, optional): Scale to calculate quintiles. Defaults to 100.

        Returns:
            tuple[ee.Image, ee.FeatureCollection]: returns the image with valid areas normalized by quintile, and a featurecollection of any invalid areas.
        '''
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

            out = quintiles \
                .where(image.lte(low),1) \
                .where(image.gt(low).And(image.lte(lowmed)),2) \
                .where(image.gt(lowmed).And(image.lte(highmed)),3) \
                .where(image.gt(highmed).And(image.lte(high)),4) \
                .where(image.gt(high),5)
            
            return out
    
        quintile_image = ee.ImageCollection(vaild_quintiles_list.map(conditions)).mosaic()
        
        return (quintile_image, invalid_regions)


    def normalize_image(self,layer, region, method='mixmax'):
        '''Normalization of an image by the region of interst

        Args:
            layer (dict): dictionary that has 'eeimage' key
            region (ee.Geometry): An earthengine geometry objet
            method (str, optional): method to normalize image. Either 'minmax' or 'quintile' . Defaults to 'mixmax'.
        '''
        eeimage = layer['eeimage']
        if method == 'minmax': 
            eeimage = self.minmax_normalization(eeimage,region)
        elif method == 'quintile':
            region_as_featurecollection = ee.FeatureCollection(region)
            eeimage = self.quintile_normalization(eeimage,region_as_featurecollection)[0]
        layer.update({'eeimage':eeimage})

    def normalize_benefits(self,benefits_layers,method='minmax'):
        
        list(map(lambda i : self.normalize_image(i,self.aoi_model.feature_collection, method), benefits_layers))

    def make_benefit_expression(self,benefits_layers):
        '''Makes the benefits portion of the WLC expression. Denoted as (Benefit_i * weight_i)+...(Benefit_n * weight_n)

        Args:
            benefits_layers (list[dict]): List of benefits 

        Returns:
           dict, str: dictionary of earthengine images for expression, string representation of the expression
        '''
        
        # build expression for benefits
        fdict_bene = {'f' + str(index): element['norm_weight'] for index, element in enumerate(benefits_layers)}
        idict_bene = {'b' + str(index): element['eeimage'] for index, element in enumerate(benefits_layers)}

        exp_bene = ['(f' + str(index) + '*b' + str(index) + ')' for index, element in enumerate(benefits_layers)]
        # i_enum = {'b'+str(index): img.select(index) for index, element in enumerate(ranks)}
        benefits_exp = '+'.join(exp_bene).join(['(', ')'])

        return fdict_bene, idict_bene, benefits_exp 

    def make_cost_expression(self,costs_layers):
        '''Makes the costs portion of the WLC expression. Denoted as (Cost_i + ... + Cost_n)

        Args:
            costs_layers(list[dict]): List of costs

        Returns:
           dict, str: dictionary of earthengine images for expression, string representation of the expression
        '''
        idict = {'c' + str(index):element['eeimage'] for index, element in enumerate(costs_layers)}
        exp = ['(c' + str(index) + ')' for index, element in enumerate(costs_layers)]
        exp_string = '+'.join(exp).join(['(', ')'])

        return idict, exp_string

    def make_constraint_expression(self,constraints_layers):
        '''Makes the constraints portion of the WLC expression. Denoted as (Constraints_i * ... * Constraint_n)

        Args:
            constraints_layers (list[dict]): List of constraints

        Returns:
           dict, str: dictionary of earthengine images for expression, string representation of the expression
        '''
        idict = {'cn' + str(index):element['eeimage'] for index, element in enumerate(constraints_layers)}
        exp = ['(cn' + str(index) + ')' for index, element in enumerate(constraints_layers)]
        exp_string = '*'.join(exp).join(['(', ')'])

        return idict, exp_string

    def make_expression(self,benefits_layers,costs_layers,constraints_layers):
        '''Makes the final expression used to calculate the WLC. The weighted sum benefits divided by the costs multiplied by constraints. 

        Args:
            benefits_layers (list[dict[]]): List of benefits 
            costs_layers (list[dict[]]): List of costs
            constraints_layers (list[dict[]]): List of constraints

        Returns:
            str, dict: string representation of the expression, dictionary of earthengine images for expression
        '''
        fdict_bene, idict_bene, benefits_exp = self.make_benefit_expression(benefits_layers)
        idict_cost, costs_exp = self.make_cost_expression(costs_layers)
        idict_cons, constraint_exp = self.make_constraint_expression(constraints_layers)

        expression_dict = {**fdict_bene, **idict_bene, **idict_cost, **idict_cons}
        expression = f"( ( {benefits_exp} / {costs_exp} ) * {constraint_exp} )"

        return expression, expression_dict

    def wlc(self):
        '''Calculates the weighted linear combination using benefits, risks, costs, and constraints. Creates ee images for each input. Normalizes benefit inputs for Aoi by quintile and normalizes weights to 0 - 1. WLC image is rescaled by the 3rd and 97th percentiles after calculation then converted to 1 - 5  scale.

        Returns:
            earthengine image: WLC restoration suitability image
        '''
        layerlist = self.rp_layers_model.layer_list
        constraints = json.loads(self.rp_questionaire_model.constraints)
        priorities = json.loads(self.rp_questionaire_model.priorities)
        
        # load layers and create eeimages
        benefits_layers = [i for i in layerlist if i['theme'] == 'benefits' and priorities[i['subtheme']] != 0]
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), benefits_layers))

        risks_layers = [i for i in layerlist if i['theme'] == 'risks']
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer'])}), risks_layers))

        costs_layers = [i for i in layerlist if i['theme'] == 'costs']
        list(map(lambda i : i.update({'eeimage':ee.Image(i['layer']).unmask() }), costs_layers))

        # constraint_layer, initialize with constant value 1 
        constraints_layers = [i for i in layerlist if i['theme'] == 'constraint']
        list(map(lambda i : i.update({'eeimage':ee.Image.constant(1)}), constraints_layers))
        constraints_layers = self.make_constraints(constraints, constraints_layers)

        self.normalize_benefits(benefits_layers, method='quintile')
        
        # normalize benefit weights to 0 - 1 
        sum_weights =sum(priorities[i['subtheme']] for i in benefits_layers)
        list(map(lambda i : i.update({'norm_weight': round( (priorities[i['subtheme']] / sum_weights), 5) }), benefits_layers))

        exp, exp_dict = self.make_expression(benefits_layers,costs_layers,constraints_layers)

        # cal wlc image
        wlc_image = ee.Image.constant(1).expression(exp,exp_dict)

        # rescale wlc image from to
        wlc_image2 = self.percentile_normalization(wlc_image,self.aoi_model.feature_collection,10000).multiply(4).add(1)

        # rather than clipping paint wlc to region
        wlc_out = ee.Image().float()
        wlc_out = wlc_out.paint(ee.FeatureCollection(self.aoi_model.feature_collection), 0).where(wlc_image2, wlc_image2).selfMask()

        setattr(self, 'wlcoutputs',(wlc_out, benefits_layers, constraints_layers, costs_layers))
        setattr(self, 'wlc_debug',(wlc_image,wlc_image2, wlc_out))
        
        return  wlc_out


