from .color_gradient import gradient, no_data_color

# vizualisation parameters of the final_layer
final_viz = {
    "min": 0,
    "max": 5,
    "palette": no_data_color + gradient(5),
}

# matplotlib viz_param but in GEE
# https://code.earthengine.google.com/?scriptPath=users%2Fgena%2Fpackages%3palettes
plt_viz = {
    "viridis": {
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
