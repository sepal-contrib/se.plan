from traitlets import HasTraits, Any, observe, dlink

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
import ee

from component.message import cm
from component import parameter as cp

ee.Initialize()


class Constraint(sw.SepalWidget, v.Row):

    custom_v_model = Any(-1).tag(sync=True)

    def __init__(
        self, widget, name="name", header="header", layer="layer", id_="id", **kwargs
    ):

        # default
        self.id = id_
        self.layer = layer
        self.header = header
        self.name = name
        self.class_ = "ma-5"
        self.widget = widget
        self.align_center = True

        # creat a pencil btn
        self.btn = v.Icon(children=["mdi-pencil"], _metadata={"layer": id_})

        # create the row
        super().__init__(**kwargs)

        self.children = [
            v.Flex(align_center=True, xs1=True, children=[self.btn]),
            v.Flex(align_center=True, xs11=True, children=[self.widget]),
        ]

        # js behaviour
        self.widget.observe(self._on_change, "v_model")

    def _on_change(self, change):

        # update the custom v_model
        # if the widget is displayed on the questionnaire
        if self.viz:
            self.custom_v_model = change["new"]

        return

    def disable(self):

        # update the custom v_model
        self.custom_v_model = -1

        # hide the component
        self.hide()

        return self

    def unable(self):

        # update the custom v_model
        self.custom_v_model = self.widget.v_model

        # show the component
        self.show()

        return self


class Binary(Constraint):
    def __init__(self, name, header, layer, **kwargs):

        # get the translated name from cm
        t_name = getattr(cm.layers, name).name

        widget = v.Switch(
            persistent_hint=True,
            v_model=True,
            label=t_name,
            **kwargs,
        )

        super().__init__(widget, name=t_name, header=header, id_=name, layer=layer)


class Range(Constraint):

    LABEL = ["low", "medium", "high"]

    def __init__(self, name, header, unit, layer, **kwargs):

        # get the translated name from cm
        t_name = getattr(cm.layers, name).name

        widget = v.RangeSlider(
            label=f"{t_name} ({unit})",
            max=1,
            step=0.1,
            v_model=[0, 1],
            thumb_label="always",
            persistent_hint=True,
            **kwargs,
        )

        super().__init__(widget, name=t_name, header=header, id_=name, layer=layer)

    def set_values(self, geometry, layer):

        # compute the min and the max for the specific geometry and layer
        ee_image = ee.Image(layer).select(0)

        # get min
        min_ = ee_image.reduceRegion(
            reducer=ee.Reducer.min(), geometry=geometry, scale=250, bestEffort=True
        )
        min_ = list(min_.getInfo().values())[0]

        # get max
        max_ = ee_image.reduceRegion(
            reducer=ee.Reducer.max(), geometry=geometry, scale=250, bestEffort=True
        )
        max_ = list(max_.getInfo().values())[0]

        # if noneType it means that my AOI is out of bounds with respect to my constraint
        # as it won't be usable I need to add a hint to the end user
        if min_ is None or max_ is None:

            self.widget.error_messages = cm.constraints.error.out_of_aoi
            self.widget.min = 0
            self.widget.max = 1
            self.widget.step = 0.1
            self.widget.v_model = [0, 1]

        else:

            # remove the error state
            self.widget.error_messages = []

            # set the min max
            self.widget.min = round(min_, 2)
            self.widget.max = round(max_, 2)

            # set the number of steps by stting the step parameter (100)
            self.widget.step = max(0.01, (self.widget.max - self.widget.min) / 100)

            # set the v_model on the "min - max" value to select the whole image by default
            self.widget.v_model = [self.widget.min, self.widget.max]

        return self


class CustomPanel(v.ExpansionPanel, sw.SepalWidget):
    def __init__(self, category, criterias):

        # save title name
        self.title = getattr(cm.constraint.category, category)

        # create a header, as nothing is selected by default it should only display the title
        self.header = v.ExpansionPanelHeader(children=[self.title])

        # link the criterias to the select
        self.criterias = [c.disable() for c in criterias if c.header == category]
        self.select = v.Select(
            disabled=True,  # disabled until the aoi is selected
            class_="mt-5",
            small_chips=True,
            v_model=[],
            items=[c.name for c in self.criterias],
            label=cm.constraints.criteria_lbl,
            multiple=True,
            deletable_chips=True,
            persistent_hint=True,
            hint=cm.constraints.error.no_aoi,
        )

        # create the content, nothing is selected by default so Select should be empty and criterias hidden
        criteria_flex = [v.Flex(xs12=True, children=[c]) for c in self.criterias]
        self.content = v.ExpansionPanelContent(
            children=[v.Layout(row=True, children=[self.select] + criteria_flex)]
        )

        # create the actual panel
        super().__init__(children=[self.header, self.content])

        # link the js behaviour
        self.select.observe(self._show_crit, "v_model")
        self.select.observe(self._on_change, "v_model")

    def _on_change(self, change):
        """remove the menu-props if at least 1 items is added"""

        if len(change["old"]) == 0:
            self.select.menu_props = {}

        return self

    def _show_crit(self, change):

        for c in self.criterias:
            if c.name in change["new"]:
                c.unable()
            else:
                c.disable()

        return self

    def expand(self):
        """when the custom panel expand I want to display only the title"""

        self.header.children = [self.title]

        # automatically open the criterias if none are selected
        if len(self.select.v_model) == 0 and self.select.disabled == False:
            self.select.menu_props = {"value": True}

        return self

    def shrunk(self):
        """when shrunked I want to display the chips int the header along the title"""

        # automatically close the criterias if none are selected
        self.select.menu_props = {}

        # get the chips
        chips = v.Flex(
            children=[
                v.Chip(class_="ml-1 mr-1", small=True, children=[c.name])
                for c in self.criterias
                if c.viz
            ]
        )

        # write the new header content
        self.header.children = [self.title, chips]

        return self
