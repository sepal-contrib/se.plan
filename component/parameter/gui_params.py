# list of the available constraints types. They will be used in the criterias names
criteria_types = ["land_use", "bio", "socio_eco", "forest"]

lc_crit = {
    "tooltip": 0,
    "layer": "land_cover",
    "header": "land_use",
    "content": "BINARY",
}
land_use_criterias = {
    "shrub": {**lc_crit, "value": 20},  # shrubs
    "herbaceous": {**lc_crit, "value": 30},  # hebaceous vegetation
    "agriculture": {**lc_crit, "value": 40},  # agriculture
    "urban": {**lc_crit, "value": 50},  # urban
    "bare": {**lc_crit, "value": 60},  # bare/sparse vegetation
    "snow": {**lc_crit, "value": 70},  # snow and ice
    "wetland": {**lc_crit, "value": 90},  # herbaceous wetland
    "moss": {**lc_crit, "value": 100},  # moss and lichen
}


# list of the available constraint criteria
# the "header" describe the category of the concstraint
# the "layer" describe the layer to use
# the "content" how it should be used
# None for binary inputs
# integer for the max of a range input
# the number of the "tooltip" text:
# 0: less than
# 1: more than
# 2 binary

# note: the duplication of layers and name is a trick to include correctly the lc
criterias = {
    **land_use_criterias,
    "annual_rainfall": {
        "tooltip": 1,
        "layer": "annual_rainfall",
        "header": "bio",
        "content": "RANGE",
    },
    "water_stress": {
        "tooltip": 1,
        "layer": "water_stress",
        "header": "bio",
        "content": "RANGE",
    },
    "elevation": {
        "tooltip": 1,
        "layer": "elevation",
        "header": "bio",
        "content": "RANGE",
    },
    "slope": {"tooltip": 1, "layer": "slope", "header": "bio", "content": "RANGE"},
    "city_access": {
        "tooltip": 1,
        "layer": "city_access",
        "header": "socio_eco",
        "content": "RANGE",
    },
    "population_density": {
        "tooltip": 1,
        "layer": "population_density",
        "header": "socio_eco",
        "content": "RANGE",
    },
    "protected_areas": {
        "tooltip": 0,
        "layer": "protected_areas",
        "header": "socio_eco",
        "content": "BINARY",
    },
    "property_rights": {
        "tooltip": 1,
        "layer": "property_rights",
        "header": "socio_eco",
        "content": "RANGE",
    },
    "deforestation_rate": {
        "tooltip": 1,
        "layer": "deforestation_rate",
        "header": "forest",
        "content": "RANGE",
    },
    "climate_risk": {
        "tooltip": 1,
        "layer": "climate_risk",
        "header": "forest",
        "content": "RANGE",
    },
    "natural_regeneration": {
        "tooltip": 1,
        "layer": "natural_regeneration",
        "header": "forest",
        "content": "RANGE",
    },
    "declining_population": {
        "tooltip": 1,
        "layer": "declining_population",
        "header": "socio_eco",
        "content": "BINARY",
    },
}
