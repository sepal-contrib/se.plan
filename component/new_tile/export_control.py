from datetime import datetime as dt
from pathlib import Path

from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from sepal_ui.scripts import gee
from sepal_ui.scripts import utils as su
import ee
import ipyvuetify as v
from ipyleaflet import WidgetControl
from matplotlib.colors import to_rgba
import rasterio as rio

from component.message import cm
from component import scripts as cs
from component import parameter as cp
from component.parameter.color_gradient import red_to_green

ee.Initialize()


class ExportView(sw.Tile):
    def __init__(self, **kwargs):

        # init the downloadable informations
        self.geometry = None
        self.dataset = None
        self.name = None
        self.aoi_name = None

        # create the useful widgets
        # align on the landsat images
        w_scale_lbl = sw.Html(tag="h4", children=[cm.export.scale])
        self.w_scale = sw.Slider(
            v_model=1000, min=10, max=2000, thumb_label="always", step=10
        )

        w_method_lbl = sw.Html(tag="h4", children=[cm.export.radio.label])
        sepal = sw.Radio(label=cm.export.radio.sepal, value="sepal")
        gee = sw.Radio(label=cm.export.radio.gee, value="gee")
        self.w_method = sw.RadioGroup(v_model="gee", row=True, children=[sepal, gee])

        super().__init__(
            id_="nested",
            title=cm.export.title,
            inputs=[
                w_scale_lbl,
                self.w_scale,
                w_method_lbl,
                self.w_method,
            ],
            btn=sw.Btn(cm.export.apply),
            alert=sw.Alert(),
        )

        # add js behaviour
        self.btn.on_event("click", self._apply)

    def set_data(self, dataset, geometry, name, aoi_name):
        """set the dataset and the geometry to allow the download"""

        self.geometry = geometry
        self.dataset = dataset
        self.name = name
        self.aoi_name = aoi_name

        # add vizualization properties to the image
        # cast to image as set is a ee.Element method
        palette = ",".join(cp.no_data_color + cp.gradient(5))
        self.dataset = ee.Image(
            dataset.set(
                {
                    "visualization_0_bands": "constant",
                    "visualization_0_max": 5,
                    "visualization_0_min": 0,
                    "visualization_0_name": "restauration index",
                    "visualization_0_palette": palette,
                    "visualization_0_type": "continuous",
                }
            )
        )

        return self

    @su.loading_button(debug=False)
    def _apply(self, *args):
        """download the dataset using the given parameters"""

        folder = Path(ee.data.getAssetRoots()[0]["id"])

        # check if a dataset is existing
        if any([self.dataset == None, self.geometry == None]):
            return self

        # set the parameters
        name = self.name or dt.now().strftime("%Y-%m-%d_%H-%M-%S")
        export_params = {
            "image": self.dataset,
            "description": name,
            "scale": self.w_scale.v_model,
            "region": self.geometry,
            "maxPixels": 1e13,
        }

        # launch the task
        if self.w_method.v_model == "gee":
            export_params.update(assetId=str(folder / name), description=f"{name}_gee")
            task = ee.batch.Export.image.toAsset(**export_params)
            task.start()
            msg = "the task have been launched in your GEE acount"
            self.alert.add_msg(msg, "success")

        elif self.w_method.v_model == "sepal":
            description = f"{name}_sepal"
            export_params.update(description=description)
            gdrive = cs.gdrive()
            files = gdrive.get_files(description)
            if files == []:
                task = ee.batch.Export.image.toDrive(**export_params)
                task.start()
                gee.wait_for_completion(description, self.alert)
                files = gdrive.get_files(description)

            # save everything in the same folder as the json file
            # no need to create it it's created when the recipe is saved
            result_dir = cp.result_dir / self.aoi_name

            tile_list = gdrive.download_files(files, result_dir)
            gdrive.delete_files(files)

            # add the colormap to each tile
            colormap = {}
            for code, color in enumerate(cp.no_data_color + cp.gradient(5)):
                colormap[code] = tuple(int(c * 255) for c in to_rgba(color))

            for tile in tile_list:
                with rio.open(tile) as f:
                    profile = f.profile

                with rio.open(tile, "r+", **profile) as dst_f:
                    dst_f.write_colormap(1, colormap)

            self.alert.add_msg(f"map exported to {result_dir}", "success")

        return self


class ExportControl(sm.MenuControl):
    def __init__(self, **kwargs):
        self.view = ExportView()
        super().__init__(
            icon_content="fa-solid fa-download", card_content=self.view, **kwargs
        )