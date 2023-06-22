# list of the available constraints types. They will be used in the criterias names
criteria_types = ["land_use", "bio", "socio_eco", "forest"]

# list of all the available benefits types, they will be used for benefits names
benefit_types = ["local_live", "wood_prod", "carbon", "bio"]

# list of the layer themes
themes = ["benefit", "constraint", "cost"]


def _crit(*args):
    """Return a dict of the criteria caracteristic.

    Args need to be given in the keys order used to reduce duplicate code.
    """
    keys = ["tooltip", "layer", "header", "content"]
    return dict(zip(keys, args))


# default crits set for land use criteria
# add an extra value to it
_lc_crit = _crit(0, "land_cover", "land_use", "BINARY")
land_use_criterias = {
    "shrub": {**_lc_crit, "value": 20},  # shrubs
    "herbaceous": {**_lc_crit, "value": 30},  # hebaceous vegetation
    "agriculture": {**_lc_crit, "value": 40},  # agriculture
    "urban": {**_lc_crit, "value": 50},  # urban
    "bare": {**_lc_crit, "value": 60},  # bare/sparse vegetation
    "snow": {**_lc_crit, "value": 70},  # snow and ice
    "wetland": {**_lc_crit, "value": 90},  # herbaceous wetland
    "moss": {**_lc_crit, "value": 100},  # moss and lichen
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
    "annual_rainfall": _crit(1, "annual_rainfall", "bio", "RANGE"),
    "water_stress": _crit(1, "water_stress", "bio", "RANGE"),
    "elevation": _crit(1, "elevation", "bio", "RANGE"),
    "slope": _crit(1, "slope", "bio", "RANGE"),
    "city_access": _crit(1, "city_access", "socio_eco", "RANGE"),
    "population_density": _crit(1, "population_density", "socio_eco", "RANGE"),
    "protected_areas": _crit(0, "protected_areas", "socio_eco", "BINARY"),
    "property_rights": _crit(1, "property_rights", "socio_eco", "RANGE"),
    "deforestation_rate": _crit(1, "deforestation_rate", "forest", "RANGE"),
    "climate_risk": _crit(1, "climate_risk", "forest", "RANGE"),
    "natural_regeneration": _crit(1, "natural_regeneration", "forest", "RANGE"),
    "declining_population": _crit(1, "declining_population", "socio_eco", "BINARY"),
}
