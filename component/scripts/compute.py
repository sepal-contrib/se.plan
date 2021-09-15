from traitlets import Unicode

import ipyvuetify as v
import ee
from sepal_ui import sepalwidgets as sw

from component import parameter as cp
from component import scripts as cs


ee.Initialize()


def add_area(feature):
    return feature.set({"rp_area": feature.geometry().area()})


def display_layer(layer, aoi_model, m):

    aoi_ee = aoi_model.feature_collection
    m.zoom_ee_object(aoi_ee.geometry())
    m.addLayer(layer.round().clip(aoi_ee.geometry()), cp.final_viz, "restoration layer")

    return
