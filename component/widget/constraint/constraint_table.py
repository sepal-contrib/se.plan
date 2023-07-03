from typing import Literal

import ee
import numpy as np

# from sepal_ui import mapping as sm
import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui.aoi import AoiModel
from sepal_ui.scripts import decorator as sd
from traitlets import List, link, observe

from component import parameter as cp
from component.message import cm
from component.model.constraint_model import ConstraintModel
from component.widget import custom_widgets as cw

from .constraint_dialog import ConstraintDialog


class ConstraintRange(sw.Layout):
    """Custom widget to allow user to select the values that will be masked out of the analysis.

    This element will be different depending on the data type of the constraint.

    continuous: a slider will be displayed to select the min and max values
    discrete: a message will be displayed to inform the user that the constraint will be used as a mask besides a swith button to change default mask value, to switch between 0 and 1.
    categorical: a select list containing all the possible values in the layer.
    """

    items = List([]).tag(sync=True)
    "list: list of possible values for Select widget"

    v_model = List([]).tag(sync=True)
    "list: value selected in the widget"

    def __init__(
        self,
        data_type: Literal["continuous", "discrete", "categorical"],
        value: list,
        layer_id: str,
    ):
        self.data_type = data_type
        self.layer_id = layer_id
        self.class_ = "d-block"
        self.attributes = {"data-layer": layer_id}

        super().__init__()

        if self.data_type == "continuous":
            w_min = sw.TextField(v_model=value[0], style_="width:3em;", xs1=True)
            w_max = sw.TextField(v_model=value[1], style_="width:3em;", xs1=True)
            slider = sw.RangeSlider(v_model=value, xs1=True, xs10=True)
            slider.class_list.add("v-no-messages")

            def transform(type_):
                """Transform method between text and slider widgets."""
                position = type_ == "min"
                return [
                    lambda min_val: [min_val, slider.v_model[position]],
                    lambda slider_vmodel: slider_vmodel[not position],
                ]

            link((w_min, "v_model"), (slider, "v_model"), transform=transform("min"))
            link((w_max, "v_model"), (slider, "v_model"), transform=transform("max"))
            link((slider, "v_model"), (self, "v_model"))

            self.widget = sw.Row(
                children=[
                    sw.Flex(children=[w_min], xs1=True),
                    sw.Flex(children=[slider], xs1=True),
                    sw.Flex(children=[w_max], xs9=True),
                ],
            )

        elif self.data_type == "discrete":
            radio_group = sw.RadioGroup(
                row=True,
                label="Value to mask out:",
                v_model=[1],
                small=True,
                children=[
                    sw.Radio(label="0", v_model=[0], xsmall=True),
                    sw.Radio(label="1", v_model=[1], xsmall=True),
                ],
            )

            self.widget = sw.Flex(
                children=[
                    radio_group,
                    "Values in the map with 0 will be masked out from the analysis",
                ]
            )

            link((radio_group, "v_model"), (self, "v_model"))

        elif self.data_type == "categorical":
            self.widget = sw.Select(
                label="cm.constraint.dialog.mask",
                multiple=True,
                items=[],
                v_model=[],
                attributes={"data-layer": layer_id},
            )

            link((self.widget, "v_model"), (self, "v_model"))

        self.children = [self.widget]

    @observe("items")
    def update_items(self, change):
        """Update items of a categorical widget when it changes."""
        if not self.data_type == "categorical":
            raise ValueError("This is not a categorical widget")

        self.widget.items = change["new"]


class ConstraintRow(sw.Html):
    _DEFAULT_LAYERS = pd.read_csv(cp.layer_list).layer_id

    def __init__(
        self,
        model: ConstraintModel,
        idx: int,
        dialog: ConstraintDialog,
        aoi_model: AoiModel,
    ) -> None:
        # get the models as a member
        self.model = model
        self.dialog = dialog
        self.aoi_model = aoi_model

        # extract information from the model
        name = self.model.names[idx]
        unit = self.model.units[idx]
        layer_id = self.model.ids[idx]
        value = self.model.values[idx]
        self.asset = self.model.assets[idx]

        # create the crud interface
        self.edit_btn = cw.TableIcon("fa-solid fa-pencil", layer_id)
        self.delete_btn = cw.TableIcon("fa-solid fa-trash-can", layer_id)
        self.edit_btn.class_list.add("mr-2")

        # create Maskout widget

        ConstraintRange(
            data_type=self.model.data_type[idx],
            value=value,
            layer_id=layer_id,
        )

        self.get_limits()

        td_list = [
            sw.Html(tag="td", children=[self.edit_btn, self.delete_btn]),
            sw.Html(tag="td", children=[name + f" ({unit})"]),
            sw.Html(tag="td", children=[self.w_maskout]),
        ]

        super().__init__(tag="tr", children=td_list)

        # add js behaviour
        self.delete_btn.on_event("click", self.on_delete)
        self.edit_btn.on_event("click", self.on_edit)

        self.w_maskout.on_event("change", self.update_value)
        self.w_maskout.observe(self.on_slide, "v_model")
        self.aoi_model.observe(self.get_limits, "updated")

    def on_delete(self, widget, data, event):
        """Remove the line from the model and trigger table update."""
        self.model.remove_constraint(widget.attributes["data-layer"])

    @sd.switch("loading", on_widgets=["dialog"])
    def on_edit(self, widget, data, event):
        """Open the dialog and load data contained in the model."""
        idx = self.model.get_index(widget.attributes["data-layer"])

        self.dialog.fill(
            theme=self.model.themes[idx],
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
            unit=self.model.units[idx],
            data_type=self.model.data_type[idx],
        )

        self.dialog.value = True

    def on_slide(self, c):
        """Update the text value when the slider is moved."""
        if len(self.w_slider.v_model) != 2:
            return
        self.w_min.v_model, self.w_max.v_model = self.w_slider.v_model
        print("on slide done")

    def update_value(self, widget, *args):
        print("update value")
        self.model.update_value(
            self.w_slider.attributes["data-layer"], self.w_slider.v_model
        )
        print("update value done")

    @sd.need_ee
    def get_limits(self, *args) -> None:
        """Get the min and max value of the asset in the aoi."""
        if not self.aoi_model.feature_collection:
            max_, min_ = (np.iinfo(np.int8).max, np.iinfo(np.int8).min)
        else:
            ee_image = ee.Image(self.asset).select(0)
            red = ee.Reducer.minMax()
            geom = self.aoi_model.feature_collection
            max_min = (
                ee_image.reduceRegion(reducer=red, geometry=geom, scale=500)
                .toArray()
                .getInfo()
            )
            max_, min_ = max(max_min), min(max_min)

        self.w_slider.min = min_
        self.w_slider.max = max_


class ConstraintTable(sw.Layout):
    def __init__(
        self, model: ConstraintModel, dialog: ConstraintDialog, aoi_model: AoiModel
    ) -> None:
        # save the model and dialog as a member
        self.model = model
        self.dialog = dialog
        self.aoi_model = aoi_model
        self.toolbar = cw.ToolBar(model, dialog)

        # create the table
        super().__init__()

        self.class_ = "d-block"

        # generate header using the translator
        headers = sw.Html(
            tag="tr",
            children=[
                sw.Html(tag="th", children=[cm.constraint.table.header.action]),
                sw.Html(tag="th", children=[cm.constraint.table.header.name]),
                sw.Html(tag="th", children=[""], style_="width: 5em;"),
                sw.Html(
                    tag="th",
                    children=[cm.constraint.table.header.parameter],
                    style_="width: 40em;",
                ),
                sw.Html(tag="th", children=[""], style_="width: 5em;"),
            ],
        )

        self.tbody = sw.Html(tag="tbody", children=[])
        self.set_rows()

        # create the table
        self.table = sw.SimpleTable(
            dense=False,
            children=[
                sw.Html(tag="thead", children=[headers]),
                self.tbody,
            ],
        )

        self.children = [self.toolbar, self.table]

        # add js behavior
        self.model.observe(self.set_rows, "updated")

    def set_rows(self, *args):
        rows = []
        for i, _ in enumerate(self.model.names):
            row = ConstraintRow(self.model, i, self.dialog, self.aoi_model)
            rows.append(row)
        self.tbody.children = rows
