from component.message import cm

# list of the available constraints types. They will be used in the criterias names 
criteria_types = {
    'land_use': cm.param.criteria_types.land_use,
    'bio': cm.param.criteria_types.bio,
    'socio_eco': cm.param.criteria_types.socio_eco,
    'forest': cm.param.criteria_types.forest
    #'treecover': 'Tree cover constraints within land cover classes',
}

# list of the available constraint criteria
# the "header" describe the category of the concstraint 
# the "layer" describe the layer to use 
# the "content" how it should be used
    # None for binary inputs 
    # dict for dropdown
    # integer for the max of a range input
# the number of the "tooltip" text:
    # 0: less than 
    # 1: more than 
    # 2 binary
criterias = {
    'Bare land': {
        'label' : cm.param.criteria.bare_land,
        'tooltip': 2,
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Shrub land': {
        'label' : cm.param.criteria.shrub_land,
        'tooltip': 2,
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Agricultural land' : {
        'label': cm.param.criteria.agriculture_land,
        'tooltip': 2,
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Annual rainfall': {
        'label' : cm.param.criteria.rainfall.name,
        'tooltip': 1,
        'layer': 'annual_rainfall',
        'header': 'bio',
        'content': [
            {'text': cm.param.criteria.rainfall.high,    'value': 1000},
            {'text': cm.param.criteria.rainfall.medium, 'value': 500},
            {'text': cm.param.criteria.rainfall.low,    'value': 200}
        ]
    },
    'Baseline water stress': {
        'label' : cm.param.criteria.water_stress.name,
        'tooltip': 0,
        'layer': 'water_stress',
        'header': 'bio',
        'content': [
            {'text': cm.param.criteria.water_stress.high, 'value':3},
            {'text': cm.param.criteria.water_stress.medium, 'value':2},
            {'text': cm.param.criteria.water_stress.low, 'value':1},      
        ]
    },
    'Elevation' : {
        'label' : cm.param.criteria.elevation.name,
        'tooltip': 1,
        'layer': 'elevation',
        'header': 'bio',
        'content': [
            {'text': cm.param.criteria.elevation.high,    'value': 3000},
            {'text': cm.param.criteria.elevation.medium, 'value': 1000},
            {'text': cm.param.criteria.elevation.low,    'value': 300},
        ]
    },
    'Slope' : {
        'label' : cm.param.criteria.slope.name,
        'tooltip': 1,
        'layer': 'slope',
        'header': 'bio',
        'content': [
            {'text': cm.param.criteria.slope.high,    'value': 25},
            {'text': cm.param.criteria.slope.medium, 'value': 10},
            {'text': cm.param.criteria.slope.low,    'value': 5},
        ]
    },
    'Accessibility to cities' : {
        'label' : cm.param.criteria.city_access.name,
        'tooltip': 0,
        'layer': 'city_access',
        'header': 'socio_eco',
        'content': [
            {'text': cm.param.criteria.city_access.high,    'value': 360},
            {'text': cm.param.criteria.city_access.medium, 'value': 180},
            {'text': cm.param.criteria.city_access.low,    'value': 60},
        ]
    },
    'Population density': {
        'label' : cm.param.criteria.population_density.name,
        'tooltip': 0,
        'layer': 'population_density',
        'header': 'socio_eco',
        'content': [
            {'text': cm.param.criteria.population_density.high,    'value': 100},
            {'text': cm.param.criteria.population_density.medium, 'value': 10},
            {'text': cm.param.criteria.population_density.low,    'value': 1},
        ]
    },
    'Protected areas' : {
        'label' : cm.param.criteria.protected_areas,
        'tooltip': 2,
        'layer': 'protected_areas',
        'header': 'socio_eco',
        'content': None
    },
    'Property rights protection' : {
        'label' : cm.param.criteria.property_rigths.name,
        'tooltip': 1,
        'layer': 'property_rigths',
        'header': 'socio_eco',
        'content': [
            {'text': cm.param.criteria.property_rigths.high,    'value': -11},
            {'text': cm.param.criteria.property_rigths.medium, 'value': -53},
            {'text': cm.param.criteria.property_rigths.low,    'value': -95},
        ]
    },
    'Deforestation rate' : {
        'label' : cm.param.criteria.deforestation_rate.name,
        'tooltip': 0,
        'layer': 'deforestation_rate',
        'header': 'forest',
        'content': [
            {'text': cm.param.criteria.deforestation_rate.high,    'value': 92},
            {'text': cm.param.criteria.deforestation_rate.medium, 'value': 43},
            {'text': cm.param.criteria.deforestation_rate.low,    'value': 21},
        ]
    },
    'Climate risk' : {
        'label' : cm.param.criteria.climate_risk.name,
        'tooltip': 1,
        'layer': 'climate_risk',
        'header': 'forest',
        'content': [
            {'text': cm.param.criteria.climate_risk.high,    'value': 25},
            {'text': cm.param.criteria.climate_risk.medium, 'value': -2},
            {'text': cm.param.criteria.climate_risk.low,    'value': -24},
        ]
    },
    'Natural regeneration variability' : {
        'label' : cm.param.criteria.natural_regeneration.name,
        'tooltip': 0,
        'layer': 'natural_regeneration',
        'header': 'forest',
        'content': [
            {'text': cm.param.criteria.natural_regeneration.high,    'value': 26},
            {'text': cm.param.criteria.natural_regeneration.medium, 'value': 16},
            {'text': cm.param.criteria.natural_regeneration.low,    'value': 10},
        ]
    },
    'Declining population': {
        'label' : cm.param.criteria.declining_population,
        'tooltip': 2,
        'layer': 'declining_population',
        'header': 'socio_eco',
        'content': None
    }
    #"Agriculture": {
    #    'layer': None,
    #    'header': 'treecover',
    #    'content': 100
    #},
    #"Rangeland": {
    #    'layer': None,
    #    'header': 'treecover',
    #    'content': 100
    #},
    #"Grassland": {
    #    'layer': None,
    #    'header': 'treecover',
    #    'content': 100
    #},
    #"Settlements": {
    #    'layer': None,
    #    'header': 'treecover',
    #    'content': 100
    #},
}