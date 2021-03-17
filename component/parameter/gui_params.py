# list of the available constraint criteria
# None for binary inputs 
# dict for dropdonw 
# integer for the max  of a range input
criterias = {
    'Bare land': None,
    'Shrub land': None,
    'Agricultural land': None,
    'Annual rainfall': [
        {'text': 'high precipitaion',    'value': 10},
        {'text': 'medium precipitaion', 'value': 5},
        {'text': 'low precipitaion',    'value': 0},
    ],
    'Population': [
        {'text': 'high populated',    'value': 10e6},
        {'text': 'medium populated', 'value': 10e3},
        {'text': 'low populated',    'value': 10},
    ],
    'Elevation': [
        {'text': 'high altitude',    'value': 1000},
        {'text': 'medium altitude', 'value': 500},
        {'text': 'low altitude',    'value': 0},
    ],
    'Slope' : [
        {'text': 'high slope',    'value': 100},
        {'text': 'medium slope', 'value': 50},
        {'text': 'low slope',    'value': 10},
    ],
    'Tree cover': 100,
    'Protected area': None,
    'Opportunity cost': [
        {'text': 'cost a lot',    'value': 100},
        {'text': 'medium cost', 'value': 50},
        {'text': 'low cost',    'value': 10},
    ],
}

# list of the available land use for the potential land use tile 
land_use = [
    "Agriculture",
    "Rangeland",
    "Grassland"
]

# list of the available goals for the goals tile
goals = [
    'Enhancement of existing areas',
    'Increase the forest cover',
    'Reflect relevant national regulations',
    'Achieve international commitments',
    'Improve connectivity and landscape biodiversity'
]

# list of the available priorities for the priority tile
priorities = [
    'Local livelihoods',
    'Wood production',
    'Non-timber tree benefits',
    'Water quality'
]