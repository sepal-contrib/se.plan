from pathlib import Path

# list of available layers for the optimisation based on the layer_list in data
layer_list = Path(__file__).parents[2] / "utils" / "layer_list.csv"

# list of the lmic countries
country_list = Path(__file__).parents[2] / "utils" / "lmic_countries.csv"

# recipe schema
recipe_schema_path = Path(__file__).parents[2] / "utils" / "recipe_schema.json"


# legends
legends_path = Path(__file__).parents[2] / "utils" / "known_legends.json"

# GAUL 2015 → 2024 code migration map
gaul_migration_map = Path(__file__).parents[2] / "utils" / "gaul_2015_to_2024.json"
