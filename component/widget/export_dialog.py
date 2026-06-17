import logging
from pathlib import Path
from typing import Literal

import ee
import rasterio as rio
from matplotlib.colors import to_rgba
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import gee
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component import scripts as cs
from component.message import cm
from component.model.recipe import Recipe
from component.scripts.aoi_geometry import _aoi_bbox
from component.scripts.gee import (
    apply_export_viz,
    get_ee_project_id,
    get_gee_recipe_folder_async,
)
from component.scripts.seplan import asset_to_image, mask_image, quintiles
from component.scripts.ui_helpers import parse_export_name
from component.widget.alert_state import Alert
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn

logger = logging.getLogger("SEPLAN")

su.init_ee()


class ExportMapDialog(BaseDialog):
    def __init__(self, recipe: Recipe, alert: Alert, **kwargs):
        super().__init__(**kwargs)

        # init the downloadable informations
        self.recipe = recipe
        self.items = []

        # create the useful widgets
        # align on the landsat images
        w_scale_lbl = sw.Html(tag="h4", children=[cm.map.dialog.export.scale])
        self.w_scale = sw.Slider(
            v_model=1000, min=10, max=2000, thumb_label="always", step=10
        )

        w_method_lbl = sw.Html(tag="h4", children=[cm.map.dialog.export.radio.label])
        sepal = sw.Radio(
            label=cm.map.dialog.export.radio.sepal, value="sepal", disabled=True
        )
        gee = sw.Radio(label=cm.map.dialog.export.radio.gee, value="gee")
        gdrive = sw.Radio(label=cm.map.dialog.export.radio.gdrive, value="gdrive")

        self.w_method = sw.RadioGroup(
            v_model="gee", row=True, children=[sepal, gee, gdrive]
        )
        self.w_asset = sw.Select(items=[], v_model=[])

        # alert + action buttons (the export button runs an async task)
        self.alert = alert or sw.Alert()
        self.btn = sw.TaskButton(cm.map.dialog.export.export, small=True, class_="mr-2")
        self.btn_cancel = TextBtn(cm.map.dialog.export.cancel, outlined=True)

        title = sw.CardTitle(children=[cm.map.dialog.export.title])

        self.content = sw.CardText(
            children=[
                self.w_asset,
                w_scale_lbl,
                self.w_scale,
                w_method_lbl,
                self.w_method,
            ]
        )
        self.actions = sw.CardActions(
            children=[
                sw.Spacer(),
                self.btn,
                self.btn_cancel,
            ]
        )

        self.children = [sw.Card(children=[title, self.content, self.actions])]

        super().__init__()

        # the export button runs the (async) export task on the GEE loop
        self.btn.configure(task_factory=self._create_export_task)
        self.btn_cancel.on_event("click", self.close_dialog)

        # Let's observe "updated" trait, this one changes only when there's change
        # in the assets (new/deleted), but later we'll skip the edit one on set_asset_items
        self.recipe.seplan.benefit_model.observe(self.set_asset_items, "updated")
        self.recipe.seplan.constraint_model.observe(self.set_asset_items, "updated")
        self.recipe.seplan.cost_model.observe(self.set_asset_items, "updated")

        self.set_asset_items()

    def set_asset_items(self, *_):
        """Set selectable widget with the available assets."""
        if self.items != self.get_asset_items():
            self.items = self.w_asset.items = self.get_asset_items()
            self.w_asset.v_model = ["index", "constraint_index"]

    def get_asset_items(self):
        """Get gee assets that are available for download."""
        # One way can be to observe all the models from the seplan model
        # and check if there's a difference between the current and the previous
        # if there's a difference, then we can update the assets item list

        index_items = [
            {"header": "Index"},
            {
                "text": cm.layer.index.constraint_index.name,
                "value": ["index", "constraint_index"],
            },
            {
                "text": cm.layer.index.benefit_cost_index.name,
                "value": ["index", "benefit_cost_index"],
            },
            {
                "text": cm.layer.index.benefit_index.name,
                "value": ["index", "benefit_index"],
            },
            {"divider": True},
        ]

        normalized_benefits = (
            [{"header": cm.layer.header.normalized_benefits}]
            + [
                {
                    "text": self.recipe.seplan.benefit_model.names[idx],
                    "value": ["benefit", id_],
                }
                for idx, id_ in enumerate(self.recipe.seplan.benefit_model.ids)
            ]
            + [{"divider": True}]
        )

        maskedout_constraints = (
            [{"header": cm.layer.header.constraints}]
            + [
                {
                    "text": self.recipe.seplan.constraint_model.names[idx],
                    "value": ["constraint", id_],
                }
                for idx, id_ in enumerate(self.recipe.seplan.constraint_model.ids)
            ]
            + [{"divider": True}]
        )

        normalized_costs = [{"header": cm.layer.header.costs}] + [
            {"text": self.recipe.seplan.cost_model.names[idx], "value": ["cost", id_]}
            for idx, id_ in enumerate(self.recipe.seplan.cost_model.ids)
        ]

        return (
            index_items + normalized_benefits + maskedout_constraints + normalized_costs
        )

    def get_ee_image(
        self, theme: Literal["index", "benefit", "constraint"], id_: str
    ) -> ee.Image:
        """Retrieve the specific image to download from seplan.

        The image will depend on the user's selection.
        """
        if theme == "index":
            return {
                "benefit_index": self.recipe.seplan.get_benefit_index,
                "benefit_cost_index": self.recipe.seplan.get_benefit_cost_index,
                "constraint_index": self.recipe.seplan.get_constraint_index,
            }[id_]()

        else:
            model = {
                "benefit": self.recipe.seplan.benefit_model,
                "constraint": self.recipe.seplan.constraint_model,
                "cost": self.recipe.seplan.cost_model,
            }[theme]

            idx = model.get_index(id=id_)
            ee_asset = asset_to_image(model.assets[idx])

            if theme == "benefit":
                return quintiles(
                    ee_asset, self.recipe.seplan.aoi_model.feature_collection
                )

            elif theme == "constraint":
                asset_id = model.assets[idx]
                data_type = model.data_type[idx]
                values = model.values[idx]

                return mask_image(
                    asset_id=asset_id, data_type=data_type, maskout_values=values
                )

            elif theme == "cost":
                # TODO: check if we have to normalize or not
                return ee_asset

    def _create_export_task(self):
        """Build the GEE task that runs the export (wired to the TaskButton)."""
        return self.recipe.gee_interface.create_task(
            func=self._export,
            key="export_map",
            on_error=lambda e: self.alert.add_msg(str(e), type_="error"),
        )

    async def _export(self):
        """Export the selected layer using awaited Earth Engine calls only."""
        aoi = self.recipe.seplan.aoi_model.feature_collection

        if not aoi:
            raise Exception(cm.questionnaire.error.no_aoi_on_map)

        if not self.recipe.recipe_session_path:
            raise Exception(cm.map.dialog.export.error.no_recipe)

        gee_interface = self.recipe.gee_interface

        # The value from the w_asset is a tuple with (theme, id_)
        theme, id_ = self.w_asset.v_model
        ee_image = self.get_ee_image(theme, id_)
        # Mask to the AOI so the bbox region below exports nodata outside it (a
        # polygon region masks to its shape, a bbox region doesn't). clip(fc)
        # rasterises per feature, so it doesn't dissolve the AOI like
        # aoi.geometry() would.
        ee_image = ee_image.clip(aoi)

        recipe_name = str(Path(self.recipe.recipe_session_path).stem)

        # set the parameters and parse the name for a better description
        name = parse_export_name("_".join(self.w_asset.v_model) + "_" + recipe_name)

        export_params = {
            "description": name,
            "scale": self.w_scale.v_model,
            "region": _aoi_bbox(aoi),
            "max_pixels": 1e13,
        }

        # resolve the user's Cloud project so the success message can deep-link
        # to the Earth Engine tasks page scoped to that project
        project_id = get_ee_project_id(gee_interface)

        # launch the task
        if self.w_method.v_model == "gee":

            recipe_gee_folder = await get_gee_recipe_folder_async(
                recipe_name, gee_interface
            )
            logger.debug(f"recipe_gee_folder>>>>>>>>>>>> {recipe_gee_folder}")
            export_params.update(
                asset_id=str(recipe_gee_folder / name), description=f"{name}"
            )

            # embed the map's visualization so the asset styles itself when
            # reloaded in se.plan / other SEPAL recipes / the Code Editor
            ee_image = await apply_export_viz(ee_image, theme, id_, aoi, gee_interface)

            await gee_interface.export_image_to_asset_async(ee_image, **export_params)

            msg = sw.Markdown(
                cm.map.dialog.export.gee_task_success.format(
                    name=name, project=project_id
                )
            )
            self.alert.add_msg(msg, "success")

        elif self.w_method.v_model == "gdrive":

            await gee_interface.export_image_to_drive_async(ee_image, **export_params)
            msg = sw.Markdown(
                cm.map.dialog.export.gee_task_success.format(
                    name=name, project=project_id
                )
            )
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
