import pandas as pd
import os

# list of the available constraint criteria
criterias = [
    'Bare land',
    'Shrub land',
    'Agricultural land',
    'Annual rainfall',
    'Population',
    'Elevation',
    'Slope',
    'Tree cover',
    'Protected area',
    'Opportunity cost'
]

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
    'Achievement of international commitments',
    'Improve connectivity - landscape biodiversity'
]

# list of the available priorities for the priority tile
priorities = [
    'Production Forest',
    ' Protected Area',
    'Community Foresty',
    'Community Protected Area',
    'Biodiversity conservation corridor',
    'Other private land or public land'
]

# list of available layers for the optimisation based on the layer_list in data 
layer_list = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'data', 'layer_list.csv')).fillna('')

# vizualisation parameters of the final_layer 
final_viz = {
  'min'    : 0.0,
  'max'    : 100.0,
  'palette': ['ffffff', 'afce56', '5f9c00', '0e6a00', '003800'],
}