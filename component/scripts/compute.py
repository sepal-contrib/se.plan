from math import isclose

from traitlets import Unicode
import ipyvuetify as v
import ee
from sepal_ui import sepalwidgets as sw

from component import parameter as cp
from component import scripts as cs
from component.message import cm


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
        dst.write(f"AOI,{','.join(cm.csv.index.labels)}\n")
        for aoi, v in area.items():
            content = [aoi]
            for j in range(1, 7):
                content.append(
                    f"{next((i['sum'] for i in v['values'] if isclose(i['image'], j)), 0):.2f}"
                )
            content.append(f"{v['total']:.2f}")
            dst.write(f"{','.join(content)}\n")

        # get results by theme
        for t in ["benefit", "cost", "constraint"]:
            dst.write(f"{cm.csv.theme[t]}\n")
            dst.write(f"layer,{','.join(aoi_names)}\n")
            for layer, v in theme[t].items():
                if all([isclose(i, 0) for i in v["values"]]):
                    continue
                value_list = []
                for i in range(len(aoi_names)):
                    value_list.append(str(v["values"][i]))
                dst.write(f"{layer},{','.join(value_list)}\n")

    return
