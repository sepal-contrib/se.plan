import ee
import ipyvuetify as v

def normalizeBands(img,region='projects/goldmine-265915/assets/lao/Houaphan'):
    # todo: remove default region and connect with init region
    try:
        # How am I going to have this variable availible...
        # region = ee.Geometry.Rectangle(app.selected_c.geometry().bounds().toGeoJSON())
        region = ee.FeatureCollection(region)
    except NameError as err:
        # region = ee.Geometry.Rectangle(app.pages.map.getBounds(), undefined, False)
        print('Motherfucker ',err)

    def rename(i):
        imin = ee.String(i).cat(preMin)
        imax = ee.String(i).cat(preMax)
        return ee.List([imin, imax])

    def mm(plist):
        plist = ee.List(plist)
        # get bandname
        fbn = ee.String(plist.get(0)).slice(0, -4)
        imgMin = ee.Image.constant(mmvalues.get(plist.get(0)))
        imgMax = ee.Image.constant(mmvalues.get(plist.get(1)))
        normImg = img.select(fbn).subtract(imgMin).divide(imgMax.subtract(imgMin))
        return normImg.toFloat();  # .rename(fbn)

    def mmUs(plist):
        plist = ee.List(plist)
        # get bandname
        fbn = ee.String(plist.get(0)).slice(0, -4)
        imgMin = ee.Number(mmvalues.get(plist.get(0)))
        imgMax = ee.Number(mmvalues.get(plist.get(1)))
        return img.select(fbn).unitScale(imgMin, imgMax).toFloat()

    mmvalues = img.reduceRegion(
        **{'reducer': ee.Reducer.minMax(), 'geometry': region, 'scale': 10000, 'maxPixels': 22e13, 'bestEffort': True,
         'tileScale': 4})
    bn = img.bandNames()
    preMax = '_max'
    preMin = '_min'
    bn = bn.map(rename)

    return ee.ImageCollection(bn.map(mmUs)).toBands()


def updateInverseBands(img, ilist):
    areThereInversBands = ee.Algorithms.IsEqual(img.select(ilist).bandNames().length().gte(1), 1)
    ee.Algorithms.If(areThereInversBands,
                     inverseRelation(img, ilist),
                     img)
    return img


def inverseRelation(img, ilist):
    bn = img.bandNames()
    tb = ee.Image(1).subtract(img.select(ilist))
    # select non inverse bands, add inverse bands to img, reorder
    return img.select(bn.removeAll(ilist)).addBands(tb).select(bn)


def loadFeatures():
    globcover = ee.Image('ESA/GLOBCOVER_L4_200901_200912_V2_3').select('landcover')
    bare = globcover.eq(200).unmask(0).select(['landcover'], ['bare'])
    shrub = globcover.eq(130).add(globcover.eq(110)).add(globcover.eq(120)) \
        .add(globcover.eq(30)).add(globcover.eq(150)) \
        .unmask(0).select(['landcover'], ['shrub'])
    ag = globcover.eq(11).add(globcover.eq(14)).add(globcover.eq(20)) \
        .unmask(0).select(['landcover'], ['ag'])
    pop = ee.Image('JRC/GHSL/P2016/POP_GPW_GLOBE_V1/2015')
    # Tree cover from Landsat VCF
    Ptree = ee.ImageCollection('GLCF/GLS_TCC').filter(ee.Filter.equals('year', 2000)).select(['tree_canopy_cover'], [
        'p_tree_canopy_cover']).mosaic()
    Ctree = ee.ImageCollection('GLCF/GLS_TCC').filter(ee.Filter.equals('year', 2010)) \
        .select(['tree_canopy_cover'], ['c_tree_canopy_cover']).mosaic()
    elevation = ee.Image('USGS/SRTMGL1_003')
    slope = ee.Terrain.slope(elevation)
    # add WDPA layer and rasterize
    wdpa_poly = ee.FeatureCollection("WCMC/WDPA/current/polygons")
    wdpa = wdpa_poly.filter(ee.Filter.neq('WDPAID', {})).reduceToImage(**{
        'properties': ['WDPAID'], 'reducer': ee.Reducer.first()}).gt(0).unmask(0).rename('wdpa')
    precip = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').filter(ee.Filter.equals('year', 2017)).first().rename(
        'rain');  # ask about date range and when it will be entered
    datamask = ee.Image('UMD/hansen/global_forest_change_2015').select('datamask') \
        .bitwiseAnd(1 << 0).eq(1);
    tcpotential = ee.Image("users/bastinjf_climate/FC_0412_b").rename('tcPotential')
    # output img or list? img for now for selecting by feature
    return ee.Image.cat([globcover, bare, shrub, pop, ag, Ptree, Ctree, elevation, slope, wdpa, precip, datamask,
                         tcpotential])  # add rain
def wlc(ranks, inverseList,region):
  img = loadFeatures()

  img = normalizeBands(img,region);

  img = updateInverseBands(img,inverseList)

  # good dict for xp
  fdict_enum = {'f' + str(index): element for index, element in enumerate(ranks)}
  idict_enum = {'b' + str(index): img.select(index) for index, element in enumerate(ranks)}

  z = {**fdict_enum, **idict_enum}


  # redo exprssion...
  exp_enum = ['(f' + str(index) + '*b' + str(index) + ')' for index, element in enumerate(ranks)]
  # i_enum = {'b'+str(index): img.select(index) for index, element in enumerate(ranks)}
  exp = '+'.join(exp_enum).join(['(', ')'])

  img = img.expression(exp, z)
  return img

# Test loading from here
class gee_compute():
    def __init__(self, aoi_content):
        self.default_rank_goals = {'Enhancement of existing areas': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                              'Increase the forest cover': [6, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0],
                              'Reflect relevant national regulations': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                              'Achievement of international commitments': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                              'Improve connectivity - landscape biodiversity': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                              }
        self.aoi_content = aoi_content

    def get_constraints(self, l):
        selected = self.aoi_content.children[1].children[0].children[0].critera_select.v_model
        lname = l.children[0].children[0].children[0]
        # Check if value is selected
        try:
            limg = l.children[0].children[0].children[0] in selected
        except TypeError as e:
            limg = []
            pass
        # gt = true, lt = false
        gt_lt = l.children[1].children[0].v_model
        # value
        v = l.children[2].children[0].v_model
        if limg:
            return {'name': lname, 'image': limg, 'mode': gt_lt, 'value': v}


    def create_res_priorities(self, l):
        if isinstance(l, v.Html):
            return
        slider_value = l.children[0].v_model
        slider_name = l.children[0].label

        return {'label': slider_name, 'value': slider_value}


    def get_res_priorities(self):
        rp_sliders = self.aoi_content.children[1].children[3].children[0].children[0].children
        res_priorities = [x for x in [*map(self.create_res_priorities, rp_sliders)] if x is not None]
        return res_priorities


    def adjust_ranks_by_slider(self, slider_val, ranks, priority):
        #     maybe get slider max from class at some point
        slider_max = 4
        slider_val_perc = slider_val / slider_max - 1

        change = [x * slider_val_perc for x in priority]
        ranks_new = [x + y for x, y in zip(ranks, change)]

        return ranks_new



    def prep_run_comp(self):
        #     get constraints
        c_values = self.aoi_content.children[1].children[0].children[0].criterias_values

        constraints = [x for x in [*map(self.get_constraints, c_values)] if x is not None]

        #     get get restoration goal
        r_goal = self.aoi_content.children[1].children[2].children[0].children[0].children[1].children[0].v_model
        if r_goal is None:
            return
        ranks = self.default_rank_goals[r_goal]

        #     adjust rank by sliders
        # get all rest priorities, will these need to be dynamic based on goal?
        prioity_1 = [-1, 1, 1, 0, -1, 1, 0, 1]
        prioity_2 = [-1, 1, 1, 0, -1, 1, 0, 1]
        prioity_3 = [-1, 1, 1, 0, -1, 1, 0, 1]
        prioity_4 = [-1, 1, 1, 0, -1, 1, 0, 1]
        prioity_5 = [-1, 1, 1, 0, -1, 1, 0, 1]
        prioity_6 = [-1, 1, 1, 0, -1, 1, 0, 1]
        p_list = [prioity_1, prioity_2, prioity_3, prioity_4, prioity_5, prioity_6]

        selected_priorities = self.get_res_priorities()

        for x, e in enumerate(p_list):
            ranks = self.adjust_ranks_by_slider(selected_priorities[x]['value'], ranks, e)
        #     remove zeros from
        model_ranks = [x if x >= 0 else 0 for x in ranks]
        return model_ranks, ranks, constraints, selected_priorities