import os
from pathlib import Path

lang = None
if 'CUSTOM_LANGUAGE' in os.environ:
    lang = os.environ['CUSTOM_LANGUAGE']

if lang == 'es':
    layer_list = Path(__file__).parents[2]/'utils'/'layer_list_es.csv'
else:
    # list of available layers for the optimisation based on the layer_list in data 
    layer_list = Path(__file__).parents[2]/'utils'/'layer_list.csv'
    
# list of the lmic countries 
country_list = Path(__file__).parents[2]/'utils'/'lmic_countries.csv'