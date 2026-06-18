from pathlib import Path

# list of available layers for the optimisation based on the layer_list in data
layer_list = Path(__file__).parents[2] / "utils" / "layer_list.csv"

# list of the lmic countries
country_list = Path(__file__).parents[2] / "utils" / "lmic_countries.csv"

# Minimum fraction of an AOI that must fall on LMIC land for the raster-based
# (ASSET/DRAW/SHAPE) check to consider it in scope. 0.5 == majority-LMIC.
# Replaces an older "100% coverage" gate that false-flagged whole LMIC
# countries (e.g. Indonesia, 99.999% LMIC) over a handful of 1 km coastline px.
MIN_LMIC_COVERAGE = 0.5

# recipe schema
recipe_schema_path = Path(__file__).parents[2] / "utils" / "recipe_schema.json"


# legends
legends_path = Path(__file__).parents[2] / "utils" / "known_legends.json"

# GAUL 2015 → 2024 code migration map
gaul_migration_map = Path(__file__).parents[2] / "utils" / "gaul_2015_to_2024.json"
