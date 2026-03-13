from pathlib import Path
from typing import Literal

# from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from sepal_ui.frontend.styles import get_theme
from traitlets import Any, Bool, Int, List, directional_link, link, observe

from component.message import cm
import logging

logger = logging.getLogger("SEPLAN")


class CustomNumber(Any):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, obj, value):
        if value in ["", None]:
            return 0

        if "." in str(value):
            try:
                return round(float(value), 4)
            except ValueError:
                return 0
        try:
            return int(value)
        except ValueError:
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
    "list: list of possible values for Select widget. When the data type is categorical."

    v_model = List([], allow_none=True).tag(sync=True)
    "list: value selected in the widget"

    min_ = Int(0).tag(sync=True)
    """int: minimum value of the slider. When the data type is continuous."""

    max_ = Int(1).tag(sync=True)
    """int: maximum value of the slider. When the data type is continuous."""

    step = Int(1).tag(sync=True)
    """int: step of the slider. When the data type is continuous."""

    has_error = Bool(False).tag(sync=True)
    """bool: whether the widget is in error state."""

    def __init__(
        self,
        data_type: Literal["continuous", "binary", "categorical"],
        layer_id: str,
        v_model: List = None,
    ):
        self.data_type = data_type
        self.layer_id = layer_id
        self.class_ = "align-center"
        self.attributes = {"data-layer": layer_id, "id": f"{layer_id}_widget"}
        self.v_model = []

        # Create message container
        self.message = sw.Html(tag="div", children=[""], class_=f"v-messages my-2")

        super().__init__()

        if self.data_type == "continuous":
            self.widget = CustomSlider()
            # before linking set the default v_model
            self.v_model = [0, 1]

            link((self.widget, "v_model"), (self, "v_model"))

        elif self.data_type == "binary":
            self.widget = sw.RadioGroup(
                row=True,
                label=cm.constraint.widget.binary.label,
                v_model=0,
                small=True,
                children=[
                    sw.Radio(label="0", v_model=0),
                    sw.Radio(label="1", v_model=1),
                ],
                hide_details=True,
            )

            # the widget standard value has to be a list, but
            def if_empty_list(value):
                if value == []:
                    return 0
                return value[0]

            # before linking set the default v_model
            self.v_model = [0]

            link(
                (self.widget, "v_model"),
                (self, "v_model"),
                transform=[lambda x: [x], if_empty_list],
            )

        elif self.data_type == "categorical":
            self.widget = sw.Select(
                label=cm.constraint.widget.categorical.label,
                multiple=True,
                items=[],
                v_model=None,
                hide_details=True,
                style_="width: 100%;",
                chips=True,
                deletable_chips=True,
                small_chips=True,
                class_="constraint-select-widget",
            )

            # before linking set the default v_model
            self.v_model = []

            link((self.widget, "v_model"), (self, "v_model"))

        self.v_model = v_model

        self.children = [
            sw.Flex(
                class_="d-block position-relative",
                children=[
                    sw.Flex(
                        class_="d-flex align-center",
                        children=[self.widget],
                    ),
                    self.message,
                ],
            )
        ]

        self.observe(self.set_message, "v_model")

        # just for the first time
        self.set_message({"new": self.v_model})
        self.observe(lambda *args: logger.debug(self.v_model), "v_model")

    def set_message(self, change=None):
        """Set message to the widget based on the data type."""

        # Use either the change data or the current value
        value = change["new"] if change else self.v_model

        logger.debug(
            f"Widget {self.layer_id} set_message called. value: {value}, data_type: {self.data_type}"
        )

        # For categorical widgets, always show the hint message regardless of v_model
        if self.data_type == "categorical":
            message_text = cm.constraint.widget.categorical.hint
            self.message.children = [message_text]
            logger.debug(
                f"Widget {self.layer_id} set categorical message: {message_text}"
            )
            return

        # Skip if no value (empty list or None) for binary and continuous
        if not value or (isinstance(value, list) and len(value) == 0):
            logger.debug(
                f"Widget {self.layer_id} set_message: no value, returning early"
            )
            return

        if self.data_type == "continuous":
            message_text = cm.constraint.widget.continuous.hint.format(
                value[0], value[1]
            )
            self.message.children = [message_text]
            logger.debug(
                f"Widget {self.layer_id} set continuous message: {message_text}"
            )

        elif self.data_type == "binary":
            # For binary, value[0] can be 0 or 1, both are valid
            if len(value) > 0:
                message_text = cm.constraint.widget.binary.hint[f"mask_{value[0]}"]
                self.message.children = [message_text]
                logger.debug(
                    f"Widget {self.layer_id} set binary message: {message_text}"
                )

    def set_loading(self, loading: bool):
        """Set the loading state of the widget.

        This method disables the widget components during loading.

        Args:
            loading: Whether the widget should be in loading state
        """
        # Disable the widget based on data type
        if self.data_type in ["binary", "categorical"]:
            # Only enable if not in error state
            self.widget.disabled = loading or self.has_error
        elif self.data_type == "continuous":
            # Only enable if not in error state
            self.widget.disabled = loading or self.has_error

        # Update message during loading
        if loading:
            self.message.children = ["Getting layer data... (may take several minutes)"]
            self.message.class_ = "v-messages my-2 info--text"
        else:
            # When loading finishes, reset to normal hint message only if no error
            if not self.has_error:
                logger.debug(
                    f"Widget {self.layer_id} loading finished, setting message. Current v_model: {self.v_model}, data_type: {self.data_type}"
                )
                self.set_message()
                self.message.class_ = "v-messages my-2"
            else:
                logger.debug(
                    f"Widget {self.layer_id} loading finished but has error, keeping error message"
                )

    def set_error(
        self, has_error: bool, error_message: str = None, disable_widget: bool = True
    ):
        """Set the error state and message of the widget.

        Args:
            has_error: Whether the widget is in error state
            error_message: Error message to display
            disable_widget: Whether to disable the widget (True for computation errors, False for validation errors)
        """
        logger.debug(
            f"Widget {self.layer_id} set_error called: has_error={has_error}, message={error_message}, disable={disable_widget}"
        )

        # Update the error state first
        self.has_error = has_error

        if has_error:
            if error_message:
                self.message.children = [error_message]
            else:
                self.message.children = ["Please configure this constraint"]
            self.message.class_ = "v-messages my-2 error--text"

            # Only disable the widget if requested (computation errors, not validation errors)
            if disable_widget:
                if self.data_type in ["binary", "categorical"]:
                    self.widget.disabled = True
                    logger.debug(
                        f"Widget {self.layer_id} ({self.data_type}): disabled main widget"
                    )
                elif self.data_type == "continuous":
                    self.widget.disabled = True
                    logger.debug(
                        f"Widget {self.layer_id} (continuous): disabled entire slider component"
                    )

        elif not has_error:
            # Reset message if no error
            self.set_message()
            self.message.class_ = "v-messages my-2"

            # Re-enable the widget when error is cleared
            if self.data_type in ["binary", "categorical"]:
                self.widget.disabled = False
                logger.debug(
                    f"Widget {self.layer_id} ({self.data_type}): enabled main widget"
                )
            elif self.data_type == "continuous":
                self.widget.disabled = False
                logger.debug(
                    f"Widget {self.layer_id} (continuous): enabled entire slider component"
                )

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

    disabled = Bool(False).tag(sync=True)
    "bool: whether the entire slider component is disabled"

    has_error = Bool(False).tag(sync=True)
    "bool: whether the widget is in error state"

    def __init__(self, **kwargs):
        self.class_ = "align-center"

        super().__init__()
        self.v_model = [0, 1]
        self.w_min = TextWidget(attributes={"id": "min"}, hide_details=True)
        self.w_max = TextWidget(attributes={"id": "max"}, hide_details=True)
        self.slider = sw.RangeSlider(
            v_model=[0, 1],
            xs1=True,
            xs10=True,
            class_="mt-4",
            validate_on_blur=True,
            hide_details=True,
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
        self.observe(self.update_disabled_state, "disabled")

    @observe("disabled")
    def update_disabled_state(self, change):
        """Update disabled state for all child widgets."""
        disabled = change["new"]
        self.slider.disabled = disabled
        self.w_min.disabled = disabled
        self.w_max.disabled = disabled

    def set_slider(self, change):
        """Set slider v_model based on self.v_model."""
        if not change["new"]:
            return

        self.slider.v_model = change["new"]

    def set_v_model(self, change):
        """Set v_model based on the w_min and w_min widgets."""
        if change["new"] in ["", None]:
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
