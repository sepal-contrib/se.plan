import re

import ee
from sepal_ui import sepalwidgets as sw
from traitlets import Any

from component.message import cm

ee.Initialize()


class Constraint(sw.Row):
    """Custom Constraint using a slider to define the used values.

    Anything between min and max will be included in the computation of the restoration index.

    Args:
        widget (v.Widget): any widget used to define the value of the constraint filter
        name (str): the name of the constraint (in translated language)
        header (str): the category of the constraint
        layer (str): the id of the layer (name and layer will only be different for the land_use layers)
        id_ (str): the id of the layer (name and layer will only be different for the land_use layers)
    """

    custom_v_model = Any(-1).tag(sync=True)
    "the custom dict v_model to transfer information to the other widgets of the application"

    def __init__(self, widget, name, header, layer, id_, **kwargs):
        # default
        self.id = id_
        self.layer = layer
        self.header = header
        self.name = name
        self.class_ = "ma-5"
        self.widget = widget
        self.align_center = True

        # creat a pencil btn
        self.btn = sw.Icon(children=["mdi-pencil"], _metadata={"layer": id_})

        # create the row
        super().__init__(**kwargs)

        self.children = [
            sw.Flex(align_center=True, xs1=True, children=[self.btn]),
            sw.Flex(align_center=True, xs11=True, children=[self.widget]),
        ]

        # js behaviour
        self.widget.observe(self._on_change, "v_model")

    def _on_change(self, change):
        """update v_model when the widget is changed."""
        # update the custom v_model
        # if the widget is displayed on the questionnaire
        if self.viz:
            self.custom_v_model = change["new"]

        return

    def disable(self):
        """overwrite disable method to set the custom_v_model to -1."""
        # update the custom v_model
        self.custom_v_model = -1

        # hide the component
        self.hide()

        return self

    def unable(self):
        """Overwrite unable method to set the custom_v_model to the widget current value.

        (kept when successively hide and show the same constraint).
        """
        # update the custom v_model
        self.custom_v_model = self.widget.v_model

        # show the component
        self.show()

        return self


class Binary(Constraint):
    """Custom Constraint using a Switch to define the used values.

    If value is 1 then we use all the ones, if not we use the 0s.

    Args:
        name (str): the id of the layer in the parameter dict
        header (str): the category of the constraints
        layer (str): the id of the layer (name and layer will only be different for the land_use layers)
    """

    def __init__(self, name, header, layer, **kwargs):
        # get the translated name from cm
        t_name = getattr(cm.layers, name).name

        widget = sw.Switch(
            persistent_hint=True,
            v_model=True,
            label=t_name,
            **kwargs,
        )

        super().__init__(widget, name=t_name, header=header, id_=name, layer=layer)


class Range(Constraint):
    """Custom Constraint using a slider to define the used values.

    Anything between min and max will be included in the computation of the restoration index.

    Args:
        name (str): the id of the layer in the parameter dict
        header (str): the category of the constraint
        unit (str): the unit of the layer
        layer (str): the id of the layer (name and layer will only be different for the land_use layers)
    """

    NB_STEPS = 1000
    "(int): the number of steps used in the sliders"

    def __init__(self, name, header, unit, layer, **kwargs):
        # get the translated name from cm
        t_name = getattr(cm.layers, name).name

        widget = sw.RangeSlider(
            label=f"{t_name} ({unit})",
            max=1,
            step=0.01,
            v_model=[0, 1],
            thumb_label="always",
            persistent_hint=True,
            **kwargs,
        )

        super().__init__(widget, name=t_name, header=header, id_=name, layer=layer)

    def set_values(self, geometry, layer, unit):
        """Compute the extreme value of the layer on the AOI and use them as min and max values of the slider.

        Use 1000 step to navigate from these values.

        Args:
            geometry (ee.Geometry): the AOI to compute min and max
            layer (str): the Asset id of the layer
            unit (str): the unit of the customized layer
        """
        # compute the min and the max for the specific geometry and layer
        ee_image = ee.Image(layer).select(0)

        # get min and max values
        min_max = ee_image.reduceRegion(
            reducer=ee.Reducer.minMax(), geometry=geometry, scale=250, bestEffort=True
        )
        max_, min_ = list(min_max.getInfo().values())

        # if noneType it means that my AOI is out of bounds with respect to my constraint
        # as it won't be usable I need to add a hint to the end user
        if any([min_ is None, max_ is None]):
            self.widget.error_messages = cm.constraints.error.out_of_aoi
            self.widget.min = 0
            self.widget.max = 1
            self.widget.v_model = [0, 1]
            self.widget.step = 0.01

        else:
            # remove the error state
            self.widget.error_messages = []

            # set the min max and steps based on the nmber of decimals
            # 1 id it's bigger than 100 else 2
            decimals = 1 if max_ > 100 else 2
            self.widget.min = round(min_, decimals)
            self.widget.max = round(max_, decimals)
            self.widget.step = 10**-decimals

            # set the v_model on the "min - max" value to select the whole image by default
            self.widget.v_model = [self.widget.min, self.widget.max]

        # update the label of the layer by replacing the unit
        # units are the only thing between parenthesis
        reg = r"\([\s\S]*\)"
        self.widget.label = re.sub(reg, f"({unit})", self.widget.label)

        return self


class CustomPanel(sw.ExpansionPanel):
    def __init__(self, category, criterias):
        # save title name
        self.title = getattr(cm.subtheme, category)

        # create a header, as nothing is selected by default it should only display the title
        self.header = sw.ExpansionPanelHeader(children=[self.title])

        # link the criterias to the select
        self.criterias = [c.disable() for c in criterias if c.header == category]
        self.select = sw.Select(
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
        criteria_flex = [sw.Flex(xs12=True, children=[c]) for c in self.criterias]
        self.content = sw.ExpansionPanelContent(
            children=[sw.Layout(row=True, children=[self.select] + criteria_flex)]
        )

        # create the actual panel
        super().__init__(children=[self.header, self.content])

        # link the js behaviour
        self.select.observe(self._show_crit, "v_model")
        self.select.observe(self._on_change, "v_model")

    def _on_change(self, change):
        """remove the menu-props if at least 1 items is added."""
        if len(change["old"]) == 0:
            self.select.menu_props = {}

        return self

    def _show_crit(self, change):
        for c in self.criterias:
            c.unable() if c.name in change["new"] else c.disable()

        return self

    def expand(self):
        """when the custom panel expand I want to display only the title."""
        self.header.children = [self.title]

        # automatically open the criterias if none are selected
        if len(self.select.v_model) == 0 and self.select.disabled is False:
            self.select.menu_props = {"value": True}

        return self

    def shrunk(self):
        """when shrunked I want to display the chips int the header along the title."""
        # automatically close the criterias if none are selected
        self.select.menu_props = {}

        # get the chips
        def chip(label):
            return sw.Chip(class_="ml-1 mr-1", small=True, children=[label])

        chips = sw.Flex(children=[chip(c.name) for c in self.criterias if c.viz])

        # write the new header content
        self.header.children = [self.title, chips]

        return self
