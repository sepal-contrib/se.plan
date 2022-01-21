from traitlets import HasTraits, Any, observe, dlink

from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
import ee

from component.message import cm
from component import parameter as cp

ee.Initialize()


class Constraint(sw.SepalWidget, v.Row):

    custom_v_model = Any(-1).tag(sync=True)

    def __init__(self, widget, name="name", header="header", id_="id", **kwargs):

        # default
        self.id = id_
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
    def __init__(self, name, header, id_, **kwargs):

        widget = v.Switch(
            # readonly = True,
            persistent_hint=True,
            v_model=True,
            label=name,
            **kwargs,
        )

        super().__init__(widget, name=name, header=header, id_=id_)


class Range(Constraint):

    LABEL = ["low", "medium", "high"]

    def __init__(self, name, header, unit, id_, **kwargs):

        widget = v.RangeSlider(
            label=f"{name} ({unit})",
            max=1,
            step=0.1,
            v_model=[0, 1],
            thumb_label="always",
            persistent_hint=True,
            **kwargs,
        )

        super().__init__(widget, name=name, header=header, id_=id_)

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

            self.widget.error_messages = "The aoi is out of the bounds of your constraint layer, use a custom one."
            self.widget.min = 0
            self.widget.max = 1
            self.widget.step = 0.1
            # self.widget.tick_labels = []
            self.widget.v_model = [0, 1]

        else:

            # remove the error state
            self.widget.error_messages = []

            # set the min max
            self.widget.min = round(min_, 2)
            self.widget.max = round(max_, 2)

            # set the number of steps by stting the step parameter (100)
            self.widget.step = max(0.01, (self.widget.max - self.widget.min) / 100)

            # display ticks label with low medium and high values
            # self.widget.tick_labels = [
            #    self.LABEL[i // 25 - 1] if i in [25, 50, 75] else "" for i in range(101)
            # ]

            # set the v_model on the "min - max" value to select the whole image by default
            self.widget.v_model = [self.widget.min, self.widget.max]

        return self


class CustomPanel(v.ExpansionPanel, sw.SepalWidget):
    def __init__(self, category, criterias):

        # save title name
        self.title = category

        # create a header, as nothing is selected by defaul it should only display the title
        self.header = v.ExpansionPanelHeader(children=[cp.criteria_types[category]])

        # link the criterias to the select
        self.criterias = [c.disable() for c in criterias if c.header == category]
        self.select = v.Select(
            disabled=True,  # disabled until the aoi is selected
            class_="mt-5",
            small_chips=True,
            v_model=None,
            items=[c.name for c in self.criterias],
            label=cm.constraints.criteria_lbl,
            multiple=True,
            deletable_chips=True,
            persistent_hint=True,
            hint="select an AOI first",
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

    def _show_crit(self, change):

        for c in self.criterias:
            if c.name in change["new"]:
                c.unable()
            else:
                c.disable()

        return self

    def expand(self):
        """when the custom panel expand I want to display only the title"""

        self.header.children = [cp.criteria_types[self.title]]

        return self

    def shrunk(self):
        """when shrunked I want to display the chips int the header along the title"""

        # get the title
        title = cp.criteria_types[self.title]

        # get the chips
        chips = v.Flex(
            children=[
                v.Chip(class_="ml-1 mr-1", small=True, children=[c.name])
                for c in self.criterias
                if c.viz
            ]
        )

        # write the new header content
        self.header.children = [title, chips]

        return self
