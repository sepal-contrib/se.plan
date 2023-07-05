from typing import Literal

import ee
import numpy as np

# from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from sepal_ui.aoi import AoiModel
from sepal_ui.scripts import decorator as sd
from traitlets import List, link, observe

from component.message import cm
from component.model.constraint_model import ConstraintModel
from component.widget import custom_widgets as cw

from .constraint_dialog import ConstraintDialog


class ConstraintWidget(sw.Layout):
    """Custom widget to allow user to select the values that will be masked out of the analysis.

    This element will be different depending on the data type of the constraint.
    """

    items = List([]).tag(sync=True)
    "list: list of possible values for Select widget"

    v_model = List([], allow_none=True).tag(sync=True)
    "list: value selected in the widget"

    def __init__(
        self,
        data_type: Literal["continuous", "discrete", "categorical"],
        layer_id: str,
        v_model: List = None,
    ):
        self.data_type = data_type
        self.layer_id = layer_id
        self.class_ = "align-center"
        self.attributes = {"data-layer": layer_id}

        super().__init__()

        if self.data_type == "continuous":
            w_min = sw.TextField(v_model=None, xs1=True)
            w_max = sw.TextField(v_model=None, xs1=True)
            slider = sw.RangeSlider(v_model=[0, 1], xs1=True, xs10=True, class_="mt-4")

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

            self.widget = sw.Flex(
                class_="d-flex",
                children=[
                    sw.Flex(children=[w_min], xs1=True),
                    sw.Flex(children=[slider], xs10=True),
                    sw.Flex(children=[w_max], xs1=True),
                ],
            )

        elif self.data_type == "binary":
            self.widget = sw.RadioGroup(
                row=True,
                label=cm.constraint.widget.binary.label,
                v_model=0,
                small=True,
                messages=[cm.constraint.widget.binary.mask_0],
                children=[
                    sw.Radio(label="0", v_model=0),
                    sw.Radio(label="1", v_model=1),
                ],
            )

            self.widget.observe(
                lambda change: setattr(
                    self.widget,
                    "messages",
                    [cm.constraint.widget.binary[f"mask_{change['new']}"]],
                ),
                "v_model",
            )

            link(
                (self.widget, "v_model"),
                (self, "v_model"),
                transform=[lambda x: [x], lambda x: x[0]],
            )

        elif self.data_type == "categorical":
            self.widget = sw.Select(
                label=cm.constraint.widget.categorical.label,
                multiple=True,
                items=[],
                v_model=None,
            )

            link((self.widget, "v_model"), (self, "v_model"))
            link((self.widget, "items"), (self, "v_model"))

        self.v_model = v_model
        self.children = [self.widget]

    @observe("items")
    def update_items(self, change):
        """Update items of a categorical widget when it changes."""
        if not self.data_type == "categorical":
            raise ValueError("This is not a categorical widget")

        self.widget.items = change["new"]


class ConstraintRow(sw.Html):
    def __init__(
        self,
        model: ConstraintModel,
        layer_id: str,
        dialog: ConstraintDialog,
        aoi_model: AoiModel,
    ) -> None:
        # get the models as a member

        self.tag = "tr"
        self.attributes = {"layer_id": layer_id}

        super().__init__()

        self.model = model
        self.dialog = dialog
        self.aoi_model = aoi_model

        idx = model.get_index(id=layer_id)

        # extract information from the model
        self.name = self.model.names[idx]
        self.unit = self.model.units[idx]
        self.layer_id = self.model.ids[idx]
        self.value = self.model.values[idx]
        self.data_type = self.model.data_type[idx]
        self.asset = self.model.assets[idx]

        self.update_view()

    def update_view(self):
        """Create the view of the widget based on the model."""
        # create the crud interface
        self.edit_btn = cw.TableIcon("fa-solid fa-pencil", self.layer_id)
        self.delete_btn = cw.TableIcon("fa-solid fa-trash-can", self.layer_id)
        self.edit_btn.class_list.add("mr-2")

        # create Maskout widget
        self.w_maskout = ConstraintWidget(
            data_type=self.data_type,
            layer_id=self.layer_id,
            v_model=self.value,
        )

        # self.get_limits()

        td_list = [
            sw.Html(tag="td", children=[self.edit_btn, self.delete_btn]),
            sw.Html(tag="td", children=[self.name + f" ({self.unit})"]),
            sw.Html(tag="td", children=[self.w_maskout]),
        ]

        self.children = td_list

        # add js behaviour
        self.delete_btn.on_event("click", self.on_delete)
        self.edit_btn.on_event("click", self.on_edit)
        self.w_maskout.observe(self.update_value, "v_model")
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

    def update_value(self, widget, *args):
        print("update value")

        self.model.update_value(self.layer_id, self.w_maskout.v_model)
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

        self.w_maskout.v_model = [min_, max_]


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
                sw.Html(
                    tag="th",
                    children=[cm.constraint.table.header.action],
                    style_="width: 5%;",
                ),
                sw.Html(
                    tag="th",
                    children=[cm.constraint.table.header.name],
                    style_="width: 35%;",
                ),
                sw.Html(
                    tag="th",
                    children=[cm.constraint.table.header.parameter],
                    style_="width: 70%;",
                ),
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
        """Add, remove or update rows in the table."""
        # We don't want to recreate all the elements of the table each time since
        # that's so expensive (specially the get_limits method)

        view_ids = [row.layer_id for row in self.tbody.children]
        model_ids = self.model.ids

        new_ids = [id_ for id_ in model_ids if id_ not in view_ids]
        old_ids = [id_ for id_ in view_ids if id_ not in model_ids]
        edited_id = (
            self.dialog.w_id.v_model if self.dialog.w_id.v_model in view_ids else False
        )
        if new_ids:
            for new_id in new_ids:
                row = ConstraintRow(self.model, new_id, self.dialog, self.aoi_model)
                self.tbody.children = self.tbody.children + [row]

        elif old_ids:
            for old_id in old_ids:
                row_to_remove = self.tbody.get_children(attr="layer_id", value=old_id)[
                    0
                ]
                self.tbody.children = [
                    row for row in self.tbody.children if row != row_to_remove
                ]
        elif edited_id:
            if edited_id:
                row_to_edit = self.tbody.get_children(attr="layer_id", value=edited_id)[
                    0
                ]
                row_to_edit.update_view()

        elif not (new_ids or old_ids or edited_id):
            rows = [
                ConstraintRow(self.model, i, self.dialog, self.aoi_model)
                for i, _ in enumerate(self.model.names)
            ]
            self.tbody.children = rows
