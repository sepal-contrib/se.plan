from traitlets import Unicode
import json
from pathlib import Path

from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from sepal_ui import color
from sepal_ui.scripts import utils as su
import pandas as pd
import ee
from ipyleaflet import WidgetControl

from component import parameter as cp
from component.message import cm

ee.Initialize()


class EditDialog(sw.Dialog):

    updated = Unicode("").tag(sync=True)  # the update traitlets

    def __init__(self, aoi_vew, model):

        # save the model
        self.model = model

        # listen to the aoi_vew to update the map
        self.view = aoi_vew

        self.init_layer = ""
        self.id = ""
        self.index = None

        # add all the standard placeholder, they will be replaced when a layer will be selected
        self.title = sw.CardTitle(children=[cm.dial.default_title])
        self.text = sw.CardText(children=[""])
        self.layer = sw.TextField(
            class_="ma-5",
            v_model=None,
            color="warning",
            outlined=True,
            label=cm.dial.layer,
        )
        self.unit = sw.TextField(
            class_="ma-5",
            v_model=None,
            color="warning",
            outlined=True,
            label=cm.dial.unit,
        )

        # add a map to display the layers
        self.m = sm.SepalMap()
        self.m.layout.height = "40vh"
        self.m.layout.margin = "2em"

        # two button will be placed at the bottom of the panel
        self.cancel = sw.Btn(cm.dial.cancel, color="primary", outlined=True)
        self.save = sw.Btn(cm.dial.save, color="primary")

        # create the init card
        action = sw.CardActions(class_="ma-5", children=[self.cancel, self.save])
        children = [self.title, self.text, self.layer, self.unit, self.m, action]
        self.card = sw.Card(children=children, class_="ma-0")

        # init the dialog
        super().__init__(
            persistent=True, value=False, max_width="50vw", children=[self.card]
        )

        # js behaviours
        self.layer.on_event("blur", self._on_layer_change)
        self.cancel.on_event("click", self._cancel_click)
        self.save.on_event("click", self._save_click)
        self.view.observe(self._update_aoi, "updated")

    @su.switch("loading", on_widgets=["card", "layer"])
    def _on_layer_change(self, widget, event, data):

        # do nothing if it's no_layer
        if widget.v_model == "no Layer":
            return self

        # replace the v_model by the init one
        if not widget.v_model:
            widget.v_model = self.init_layer

        # if the layer is different than the init one
        elif widget.v_model != self.init_layer:

            # display it on the map
            geometry = self.view.model.feature_collection
            image = Path(widget.v_model)

            # if the map cannot be displayed then return to init
            try:
                self.display_on_map(image, geometry)
            except Exception as e:
                widget.v_model = self.init_layer

        return self

    def _cancel_click(self, widget, data, event):

        # close without doing anything
        self.value = False
        self.updated = ""

        return

    @su.switch("loading", on_widgets=["save", "cancel"])
    def _save_click(self, widget, data, event):

        # change the model according to the selected informations
        self.model.layer_list[self.index].update(
            layer=self.layer.v_model, unit=self.unit.v_model
        )

        # modify update to tell the rest of the app that value have been changed
        self.updated = self.id

        # close
        self.value = False

        return

    def _update_aoi(self, change):

        # get the aoi
        aoi_ee = self.view.model.feature_collection

        # draw an outline
        outline = ee.Image().byte().paint(featureCollection=aoi_ee, color=1, width=3)

        # update the map
        self.m.addLayer(outline, {"palette": color.accent}, "aoi")
        self.m.zoom_ee_object(aoi_ee.geometry())

        return

    @su.switch("loading", on_widgets=["card"])
    def set_dialog(self, layer_id=None):

        # show the dialog
        self.value = True

        # remove the images
        for l in self.m.layers:
            if not (l.name in ["aoi", "CartoDB.DarkMatter", "CartoDB.Positron"]):
                self.m.remove_layer(l)

        # disable the updated value
        # to trigger the change on exit
        self.updated = ""

        # if data are empty
        if not layer_id:

            # default variables
            self.id = ""
            self.index = None
            self.init_layer = ""

            # default title
            self.title.children = [cm.dial.no_layer]

            # default text
            self.text.children = [cm.dial.disc]

            # mute all the widgets
            self.layer.v_model = cm.dial.no_layer
            self.layer.disabled = True

            self.unit.v_model = cm.dial.no_unit
            self.unit.disabled = True

            # disable save
            self.save.disabled = True

        else:

            # find the index of the item to modify in the model
            self.index = next(
                (i, l)
                for i, l in enumerate(self.model.layer_list)
                if l["id"] == layer_id
            )[0]
            self.id = layer_id

            # change title
            self.title.children = [getattr(cm.layers, layer_id).name]

            # get the layer list pd dataframe
            layer_list = pd.read_csv(cp.layer_list).fillna("")

            # change text
            layer_df_line = layer_list[layer_list.layer_id == layer_id].iloc[0]
            self.text.children = [getattr(cm.layers, layer_id).detail]

            # enable textFields
            self.layer.disabled = False
            self.layer.v_model = self.model.layer_list[self.index]["layer"]

            self.unit.disabled = False
            self.unit.v_model = self.model.layer_list[self.index]["unit"]

            # change default layer name
            self.init_layer = layer_df_line.gee_asset

            # add the custom layer if existing
            geometry = self.view.model.feature_collection
            is_default = self.layer.v_model == self.init_layer
            image = self.init_layer if is_default else self.layer.v_model
            self.display_on_map(image, geometry)

            # enable save
            self.save.disabled = False

        return

    def display_on_map(self, image, geometry):
        """
        Display the image on the map

        Args:
            image (str): the asset name of the image
            geometry (ee.Geometry): the geometry of the AOI
        """

        # clip image
        ee_image = ee.Image(image).clip(geometry)
        print(image)

        # get minmax
        min_max = ee_image.reduceRegion(
            reducer=ee.Reducer.minMax(), geometry=geometry, scale=250, bestEffort=True
        )
        max_, min_ = min_max.getInfo().values()

        min_ = 0 if min_ is None else min_
        max_ = 1 if max_ is None else max_

        # update viz_params acordingly
        viz_params = cp.plt_viz["viridis"]
        viz_params.update(min=min_, max=max_)

        # create a colorbar
        for c in self.m.controls:
            type(c) != WidgetControl or self.m.remove_control(c)
        self.m.add_colorbar(
            colors=cp.plt_viz["viridis"]["palette"],
            vmin=round(min_, 2),
            vmax=round(max_, 2),
        )

        # dispaly on map
        self.m.addLayer(ee_image, viz_params, Path(image).stem)

        return self
