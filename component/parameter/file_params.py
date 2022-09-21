from pathlib import Path

# list of available layers for the optimisation based on the layer_list in data
layer_list = Path(__file__).parents[2] / "utils" / "layer_list.csv"

# list of the lmic countries
country_list = Path(__file__).parents[2] / "utils" / "lmic_countries.csv"

# forest carbon parameters
carbon_json = Path(__file__).parents[2] / "utils" / "carbon_growth_params.json"
