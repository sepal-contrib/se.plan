# list of the available constraints types. They will be used in the criterias names 
criteria_types = {
    'land_use': 'Land use constraints',
    'bio': 'Biophysical constraints',
    'socio_eco': 'Socio-economic constraints',
    #'treecover': 'Tree cover constraints within land cover classes',
    'forest': 'Forest change'
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
        'tooltip': 2,
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Shrub land': {
        'tooltip': 2,
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Agricultural land': {
        'tooltip': 2,
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Annual rainfall': {
        'tooltip': 1,
        'layer': 'annual_rainfall',
        'header': 'bio',
        'content': [
            {'text': 'high precipitaion',    'value': 1000},
            {'text': 'medium precipitaion', 'value': 500},
            {'text': 'low precipitaion',    'value': 200}
        ]
    },
    'Baseline water stress': {
        'tooltip': 0,
        'layer': 'water_stress',
        'header': 'bio',
        'content': [
            {'text': 'high water stress', 'value':3},
            {'text': 'medium water stress', 'value':2},
            {'text': 'low water stress', 'value':1},      
        ]
    },
    'Elevation': {
        'tooltip': 1,
        'layer': 'elevation',
        'header': 'bio',
        'content': [
            {'text': 'high altitude',    'value': 3000},
            {'text': 'medium altitude', 'value': 1000},
            {'text': 'low altitude',    'value': 300},
        ]
    },
    'Slope': {
        'tooltip': 1,
        'layer': 'slope',
        'header': 'bio',
        'content': [
            {'text': 'high slope',    'value': 25},
            {'text': 'medium slope', 'value': 10},
            {'text': 'low slope',    'value': 5},
        ]
    },
    'Accessibility to cities' : {
        'tooltip': 0,
        'layer': 'city_access',
        'header': 'socio_eco',
        'content': [
            {'text': 'high acessibility',    'value': 360},
            {'text': 'medium acessibility', 'value': 180},
            {'text': 'low acessibility',    'value': 60},
        ]
    },
    'Population density' : {
        'tooltip': 0,
        'layer': 'population_density',
        'header': 'socio_eco',
        'content': [
            {'text': 'high populated',    'value': 100},
            {'text': 'medium populated', 'value': 10},
            {'text': 'low populated',    'value': 1},
        ]
    },
    'Protected areas': {
        'tooltip': 2,
        'layer': 'protected_areas',
        'header': 'socio_eco',
        'content': None
    },
    'Property rights protection': {
        'tooltip': 1,
        'layer': 'property_rigths',
        'header': 'socio_eco',
        'content': [
            {'text': 'high variation',    'value': -11},
            {'text': 'medium variation', 'value': -53},
            {'text': 'low variation',    'value': -95},
        ]
    },
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
    'Deforestation rate':{
        'tooltip': 0,
        'layer': 'deforestation_rate',
        'header': 'forest',
        'content': [
            {'text': 'high change',    'value': 92},
            {'text': 'medium change', 'value': 43},
            {'text': 'low change',    'value': 21},
        ]
    },
    'Climate risk': {
        'tooltip': 1,
        'layer': 'climate_risk',
        'header': 'forest',
        'content': [
            {'text': 'high climate risk',    'value': 25},
            {'text': 'medium climate risk', 'value': -2},
            {'text': 'low climate risk',    'value': -24},
        ]
    },
    'Natural regeneration variability': {
        'tooltip': 0,
        'layer': 'natural_regeneration',
        'header': 'forest',
        'content': [
            {'text': 'high variation',    'value': 26},
            {'text': 'medium variation', 'value': 16},
            {'text': 'low variation',    'value': 10},
        ]
    },
    'Declining population': {
        'tooltip': 2,
        'layer': 'declining_population',
        'header': 'socio_eco',
        'content': None
    }
}