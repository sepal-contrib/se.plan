from component.scripts.colors import gradient

palettes = {"green": ["#EBFAF2", "#66c2a4", "#006d2c"]}
# palettes = {"green": ["#98FB98", "#32CD32", "#006400"]}

no_data_color = ["#353535"]  # the color used for values filtered by constraints
gradient_palette = gradient(levels=5, palette=palettes["green"])

# vizualisation parameters of the final_layer
final_viz = {
    "min": 0,
    "max": 5,
    "palette": no_data_color + gradient_palette,
}

SUITABILITY_COLORS = {
    suit_code: suit_color
    for suit_code, suit_color in enumerate(gradient_palette + no_data_color, 1)
}

# matplotlib viz_param but in GEE
# https://code.earthengine.google.com/?scriptPath=users%2Fgena%2Fpackages%3palettes
map_vis = {
    "gradient": {
        "min": 0,
        "max": 10,
        "palette": [
            "#440154",
            "#433982",
            "#30678D",
            "#218F8B",
            "#36B677",
            "#8ED542",
            "#FDE725",
        ],
    },
    "binary": {
        "min": 0,
        "max": 1,
        "palette": ["#440154", "#FDE725"],
        "names": ["Masked", "Valid"],
    },
}


# the vizaulization paramters for aoi
aoi_style = {  # default styling of the layer
    "stroke": True,
    "color": "black",
    "weight": 1,
    "opacity": 1,
    "fill": True,
    "fillColor": "black",
    "fillOpacity": 0.05,
}

PLOT_COLORS = {
    "opportunity_cost": {"light": "#4CAF50", "dark": "#4CAF50"},
    "implementation_cost": {"light": "#2196F3", "dark": "#2196F3"},
}
