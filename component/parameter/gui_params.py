# list of the available constraints types. They will be used in the criterias names 
criteria_types = {
    'land_use': 'Land use constraints',
    'bio': 'Biophysical constraints',
    'socio_eco': 'Socio-economic constraints',
    'treecover': 'Tree cover constraints within land cover classes',
    'env': 'Environmental indicators',
    'no_money': 'Non-monetary'
}

# list of the available constraint criteria
# the "header" describe the category of the concstraint 
# the "layer" describe the layer to use 
# the "content" how it should be used
    # None for binary inputs 
    # dict for dropdown
    # integer for the max of a range input
criterias = {
    'Bare land': {
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Shrub land': {
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Agricultural land': {
        'layer': None,
        'header': 'land_use',
        'content': None
    },
    'Annual rainfall': {
        'layer': 'annual_rainfall',
        'header': 'bio',
        'content': [
            {'text': 'high precipitaion',    'value': 5000},
            {'text': 'medium precipitaion', 'value': 2000},
            {'text': 'low precipitaion',    'value': 500}
        ]
    },
    'Water stress': {
        'layer': 'water_stress',
        'header': 'bio',
        'content': [
            {'text': 'very high water stress', 'value':5},
            {'text': 'high water stress', 'value':4},
            {'text': 'medium water stress', 'value':3},
            {'text': 'some water stress', 'value':2},
            {'text': 'little water stress', 'value':1},            
        ]
    },
    'Elevation': {
        'layer': 'elevation',
        'header': 'bio',
        'content': [
            {'text': 'high altitude',    'value': 1000},
            {'text': 'medium altitude', 'value': 750},
            {'text': 'low altitude',    'value': 500},
        ]
    },
    'Slope': {
        'layer': 'slope',
        'header': 'bio',
        'content': [
            {'text': 'high slope',    'value': 25},
            {'text': 'medium slope', 'value': 17},
            {'text': 'low slope',    'value': 10},
        ]
    },
    'Accessibility to cities' : {
        'layer': 'city_access',
        'header': 'socio_eco',
        'content': [
            {'text': 'high acessibility',    'value': 180},
            {'text': 'medium acessibility', 'value': 600},
            {'text': 'low acessibility',    'value': 103},
        ]
    },
    'Population density' : {
        'layer': 'population_density',
        'header': 'socio_eco',
        'content': [
            {'text': 'high populated',    'value': 100},
            {'text': 'medium populated', 'value': 55},
            {'text': 'low populated',    'value': 10},
        ]
    },
    'Protected areas': {
        'layer': 'protected_areas',
        'header': 'socio_eco',
        'content': None
    },
    'Land opportunity cost': {
        'layer': 'opportunity_cost',
        'header': 'socio_eco',
        'content': [
            {'text': 'cost a lot',    'value': 100},
            {'text': 'medium cost', 'value': 50},
            {'text': 'low cost',    'value': 10},
        ]
    },
    'Property rights': {
        'layer': 'property_rigths',
        'header': 'socio_eco',
        'content': [
            {'text': 'high variation',    'value': -12},
            {'text': 'medium variation', 'value': -53},
            {'text': 'low variation',    'value': -95},
        ]
    },
    "Agriculture": {
        'layer': None,
        'header': 'treecover',
        'content': 100
    },
    "Rangeland": {
        'layer': None,
        'header': 'treecover',
        'content': 100
    },
    "Grassland": {
        'layer': None,
        'header': 'treecover',
        'content': 100
    },
    "Settlements": {
        'layer': None,
        'header': 'treecover',
        'content': 100
    },
    'Deforestation rate':{
        'layer': 'deforestation_rate',
        'header': 'env',
        'content': [
            {'text': 'high change',    'value': 40},
            {'text': 'medium change', 'value': 20},
            {'text': 'low change',    'value': 0},
        ]
    },
    'Climate risk': {
        'layer': 'climate_risk',
        'header': 'env',
        'content': [
            {'text': 'high climate risk',    'value': 25},
            {'text': 'medium climate risk', 'value': -2},
            {'text': 'low climate risk',    'value': -24},
        ]
    },
    'Natural regeneration probability': {
        'layer': 'natural_regeneration',
        'header': 'no_money',
        'content': [
            {'text': 'high variation',    'value': 26},
            {'text': 'medium variation', 'value': 22},
            {'text': 'low variation',    'value': 19},
        ]
    },
    'Declining population': {
        'layer': 'declining_population',
        'header': 'no_money',
        'content': None
    }
}