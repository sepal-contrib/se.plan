from component.message import cm

# list of the available constraints types. They will be used in the criterias names
criteria_types = ["land_use", "bio", "socio_eco", "forest"]

# list of all the available benefits types, they will be used for benefits names
benefit_types = ["local_live", "wood_prod", "carbon", "bio"]

# list of the layer themes
themes = ["benefit", "constraint", "cost"]

# list of data types
data_types = ["continuous", "categorical", "binary"]

# questionaire table headers.
table_headers = {
    "benefit": {
        "action": cm.benefit.table.header.action,
        "theme": cm.benefit.table.header.theme,
        "indicator": cm.benefit.table.header.indicator,
        "no_importance": cm.benefit.table.header.no_importance,
        "low_importance": cm.benefit.table.header.low_importance,
        "neutral": cm.benefit.table.header.neutral,
        "important": cm.benefit.table.header.important,
        "very_important": cm.benefit.table.header.very_important,
    },
    "constraint": {
        "action": cm.constraint.table.header.action,
        "name": cm.constraint.table.header.name,
        "parameter": cm.constraint.table.header.parameter,
    },
    "cost": {
        # TODO: create heir own cost translation file
        "action": cm.cost.table.header.action,
        "indicator": cm.cost.table.header.indicator,
    },
}

custom_geom_table_headers = {
    "action": cm.custom_geom.header.action,
    "name": cm.custom_geom.header.name,
}

mandatory_layers = {
    "benefit": [],
    "constraint": ["treecover_with_potential"],
    "cost": ["opportunity_cost", "implementation_cost"],
}


SUITABILITY_LEVELS = {
    1: "Very low",
    2: "Low",
    3: "Medium",
    4: "High",
    5: "Very High",
    6: "Unsuitable land",
}
