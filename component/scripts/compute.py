from math import isclose

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


def export_as_csv(area, theme, dst):

    with dst.open("w") as dst:

        # get the aoi name list
        aoi_names = [aoi for aoi in area]

        # write the suitability index results per each AOI
        dst.write("suitability\n")
        dst.write("AOI,very low,low,medium,high,very high, unsuitable, total\n")
        for aoi, v in area.items():
            VERY_LOW = next(i["sum"] for i in v["values"] if isclose(i["image"], 1))
            LOW = next(i["sum"] for i in v["values"] if isclose(i["image"], 2))
            MEDIUM = next(i["sum"] for i in v["values"] if isclose(i["image"], 3))
            HIGH = next(i["sum"] for i in v["values"] if isclose(i["image"], 4))
            VERY_HIGH = next(i["sum"] for i in v["values"] if isclose(i["image"], 5))
            UNSUITABLE = next(i["sum"] for i in v["values"] if isclose(i["image"], 6))
            TOTAL = v["total"]
            dst.write(f"{aoi},{VERY_LOW},{LOW},{MEDIUM},{HIGH},{VERY_HIGH},{TOTAL}\n")

        # write the priorities
        dst.write("priorities\n")
        dst.write(f"layer,{','.join(aoi_names)}\n")
        for layer, v in theme["benefit"].items():
            value_list = []
            for i in range(len(aoi_names)):
                value_list.append(str(v["values"][i]))
            dst.write(f"{layer},{','.join(value_list)}\n")

        # write the costs
        dst.write("costs\n")
        dst.write(f"layer,{','.join(aoi_names)}\n")
        for layer, v in theme["cost"].items():
            value_list = []
            for i in range(len(aoi_names)):
                value_list.append(str(v["values"][i]))
            dst.write(f"{layer},{','.join(value_list)}\n")

        # write the constraints
        dst.write("constraints\n")
        dst.write(f"layer,{','.join(aoi_names)}\n")
        for layer, v in theme["constraint"].items():
            value_list = []
            for i in range(len(aoi_names)):
                value_list.append(str(v["values"][i]))
            dst.write(f"{layer},{','.join(value_list)}\n")

    return
