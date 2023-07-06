# ruff: noqa: E722

from typing import Literal

# from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from traitlets import Any, Int, List, directional_link, link, observe

from component.message import cm


class CustomNumber(Any):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, obj, value):
        if value in ["", None]:
            return 0

        if "." in str(value):
            try:
                return round(float(value), 4)
            except:
                return 0
        try:
            return int(value)
        except:
            return 0


class TextWidget(sw.TextField):
    v_model = CustomNumber().tag(sync=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.v_model = None
        self.xs1 = True


class ConstraintWidget(sw.Layout):
    """Custom widget to allow user to select the values that will be masked out of the analysis.

    This element will be different depending on the data type of the constraint.
    """

    items = List([]).tag(sync=True)
    "list: list of possible values for Select widget"

    v_model = List([], allow_none=True).tag(sync=True)
    "list: value selected in the widget"

    min_ = Int(0).tag(sync=True)

    max_ = Int(1).tag(sync=True)

    step = Int(1).tag(sync=True)

    def __init__(
        self,
        data_type: Literal["continuous", "binary", "categorical"],
        layer_id: str,
        v_model: List = None,
    ):
        self.data_type = data_type
        self.layer_id = layer_id
        self.class_ = "align-center"
        self.attributes = {"data-layer": layer_id}
        self.v_model = []

        super().__init__()

        if self.data_type == "continuous":
            self.widget = CustomSlider()

            link((self.widget, "v_model"), (self, "v_model"))

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

            directional_link((self.widget, "v_model"), (self, "v_model"))

        self.v_model = v_model
        self.children = [self.widget]

    @observe("items")
    def update_items(self, change):
        """Update items of a categorical widget when it changes."""
        if not self.data_type == "categorical":
            raise ValueError("This is not a categorical widget")

        self.widget.items = change["new"]


class CustomSlider(sw.Layout):
    """Custom widget to allow user to select the values that will be masked out of the analysis.

    This element will be different depending on the data type of the constraint.
    """

    items = List([]).tag(sync=True)
    "list: list of possible values for Select widget"

    v_model = List([0, 1], allow_none=True).tag(sync=True)
    "list: value selected in the widget"

    min_ = Int(0).tag(sync=True)
    "int: minimum value of the slider"

    max_ = Int(1).tag(sync=True)
    "int: maximum value of the slider"

    step = Int(1).tag(sync=True)
    "int: step of the slider"

    def __init__(self, **kwargs):
        self.class_ = "align-center"

        super().__init__()
        self.v_model = [0, 1]
        self.w_min = TextWidget(attributes={"id": "min"})
        self.w_max = TextWidget(attributes={"id": "max"})
        self.slider = sw.RangeSlider(
            v_model=[0, 1],
            xs1=True,
            xs10=True,
            class_="mt-4",
            validate_on_blur=True,
            track_color="red",
            track_fill_color="green",
        )

        self.children = [
            sw.Flex(
                class_="d-flex",
                children=[
                    sw.Flex(children=[self.w_min], xs1=True),
                    sw.Flex(children=[self.slider], xs10=True),
                    sw.Flex(children=[self.w_max], xs1=True),
                ],
            )
        ]

        directional_link((self, "min_"), (self.slider, "min"))
        directional_link((self, "max_"), (self.slider, "max"))
        directional_link((self, "step"), (self.slider, "step"))

        self.slider.observe(self.set_min_max, "v_model")

        self.w_min.observe(self.set_v_model, "v_model")
        self.w_max.observe(self.set_v_model, "v_model")
        self.observe(self.set_slider, "v_model")

    def set_slider(self, change):
        if not change["new"]:
            return

        self.slider.v_model = change["new"]

    def set_v_model(self, change):
        """Set v_model based on the w_min and w_min."""
        if not change["new"]:
            return

        new_val = change["new"]
        widget = change["owner"]
        position = widget.attributes["id"] == "max"

        new_v_model = self.v_model[:]
        new_v_model[position] = new_val

        self.v_model = new_v_model

    def set_min_max(self, change):
        """Set min and max values to widgets."""
        self.w_min.v_model = change["new"][0]
        self.w_max.v_model = change["new"][1]
