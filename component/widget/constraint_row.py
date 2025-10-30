from pathlib import Path
import traceback
from typing import Union

import ipyvuetify as v
from ipywidgets import DOMWidget
from ipywidgets.widgets.widget import widget_serialization
from component.widget.constraint_dialog import ConstraintDialog
from component.widget.preview_map_dialog import PreviewMapDialog
from sepal_ui.scripts import decorator as sd
from sepal_ui.scripts.gee_interface import GEEInterface
from sepal_ui.scripts.gee_task import GEETask
from traitlets import Bool, Instance, List, Unicode, observe

import component.parameter.gui_params as cp
import component.scripts.gee as gee
from component.message import cm
from component.model.aoi_model import SeplanAoi
from component.model.constraint_model import ConstraintModel
from component.scripts.seplan import asset_to_image, mask_image
from component.scripts.ui_helpers import get_categorical_values
from component.scripts.validation import (
    extract_task_error,
    get_short_traceback,
    validate_constraint_values,
)
from component.widget.alert_state import Alert
from component.widget.constraint_widget import ConstraintWidget

import logging

logger = logging.getLogger("SEPLAN")


class ConstraintRow(v.VuetifyTemplate):
    """Vue-based constraint row with integrated progress bar and embedded widget."""

    template_file = str(Path(__file__).parent / "vue" / "ConstraintRow.vue")

    layer_id = Unicode("").tag(sync=True)
    layer_name = Unicode("").tag(sync=True)
    layer_unit = Unicode("").tag(sync=True)
    is_loading = Bool(False).tag(sync=True)
    has_error = Bool(False).tag(sync=True)

    constraint_widget = List(Instance(DOMWidget), default_value=[]).tag(
        sync=True, **widget_serialization
    )

    limits_completed = Bool(False)
    limits_error = Bool(False)
    error_message = Unicode("").tag(sync=True)
    error_type = Unicode("")  # "validation" or "computation"

    def __init__(
        self,
        model: ConstraintModel,
        layer_id: str,
        dialog: ConstraintDialog,
        aoi_model: SeplanAoi,
        alert: Alert,
        preview_map: PreviewMapDialog,
        gee_interface: GEEInterface,
        **kwargs,
    ):
        self.model = model
        self.dialog = dialog
        self.preview_map = preview_map
        self.aoi_model = aoi_model
        self.alert = alert
        self.gee_interface = gee_interface
        self._limits_task: GEETask = None

        # Set layer ID first
        self.layer_id = layer_id

        # Get model data
        self.get_model_data()

        # Create constraint widget
        self.w_maskout = ConstraintWidget(
            data_type=self.data_type,
            layer_id=self.layer_id,
            v_model=self.value,
        )

        # Set constraint widget as component
        self.constraint_widget = [self.w_maskout]

        # Set up observers BEFORE calling super().__init__()
        self.w_maskout.observe(self.update_value, "v_model")
        self.aoi_model.observe(self.set_limits, "updated")

        super().__init__(**kwargs)

        # Create the reusable limits task
        self._create_limits_task()

        # Start loading limits (validation will happen after loading completes)
        self.set_initial_loading()

    def validate_initial_values(self):
        """Validate constraint values when the row is first created."""
        is_valid, error_msg = self.validate_constraint_values()
        if not is_valid:
            # Set validation error state but don't disable widget
            self.has_error = True
            self.error_message = error_msg
            self.error_type = "validation"

    def validate_current_values(self):
        """Validate current constraint values and update error state."""
        is_valid, error_msg = self.validate_constraint_values()
        if not is_valid:
            # Set validation error state but don't disable widget
            self.has_error = True
            self.error_message = error_msg
            self.error_type = "validation"
        else:
            # Clear validation error state only if it was a validation error
            if self.error_type == "validation":
                self.has_error = False
                self.error_message = ""
                self.error_type = ""

    def get_model_data(self):
        """Get and set the data of the given layer_id to the row."""
        idx = self.model.get_index(self.layer_id)

        self.layer_name = self.model.names[idx]
        self.layer_unit = self.model.units[idx]
        self.value = self.model.values[idx]
        self.data_type = self.model.data_type[idx]
        self.asset = self.model.assets[idx]

    def set_initial_loading(self):
        """Set initial loading state and start loading limits."""
        self.is_loading = True
        self.set_limits()

    @observe("is_loading")
    def _on_loading_change(self, change):
        """Observer for loading state changes."""
        loading = change["new"]
        self.w_maskout.set_loading(loading)

    @observe("has_error")
    def _on_error_change(self, change):
        """Observer for error state changes."""
        self._update_widget_error_state()

    @observe("error_message", "error_type")
    def _on_error_details_change(self, change):
        """Observer for error message and type changes."""
        self._update_widget_error_state()

    def _update_widget_error_state(self):
        """Update the widget error state based on current error properties."""
        if hasattr(self, "w_maskout") and self.w_maskout:
            if self.has_error:
                error_text = self.error_message
                # Determine if widget should be disabled based on error type
                disable_widget = self.error_type == "computation"
                self.w_maskout.set_error(
                    self.has_error,
                    error_message=error_text,
                    disable_widget=disable_widget,
                )
            else:
                self.w_maskout.set_error(False, error_message="", disable_widget=False)

    def vue_on_edit(self, *_):
        """Handle edit button click from Vue."""
        self.on_edit()

    def vue_on_show_map(self, *_):
        """Handle show map button click from Vue."""
        self.on_show_map()

    def vue_on_delete(self, *_):
        """Handle delete button click from Vue."""
        self.on_delete()

    @sd.catch_errors()
    def on_edit(self, *_):
        """Open the dialog and load data contained in the model."""
        idx = self.model.get_index(self.layer_id)

        self.dialog.fill(
            theme=self.model.themes[idx],
            name=self.model.names[idx],
            id=self.model.ids[idx],
            asset=self.model.assets[idx],
            desc=self.model.descs[idx],
            unit=self.model.units[idx],
            data_type=self.model.data_type[idx],
        )
        self.dialog.open_dialog(type_="edit")

    def validate_constraint_values(self) -> tuple[bool, str]:
        """Validate current constraint values and return (is_valid, error_message)."""
        return validate_constraint_values(self.value, self.data_type, self.layer_name)

    def is_ready_for_calculation(self) -> bool:
        """Check if this constraint is ready for use in calculations (dashboard, export)."""
        is_valid, _ = self.validate_constraint_values()
        return is_valid and not self.has_error and not self.limits_error

    @sd.catch_errors()
    def on_show_map(self):
        """Mask constraint with map values and add it to the map."""
        # Pre-validate constraint values
        is_valid, error_msg = self.validate_constraint_values()
        if not is_valid:
            raise ValueError(error_msg)

        masked_layer = mask_image(self.asset, self.data_type, self.value)
        base_layer = (
            asset_to_image(self.asset)
            if self.data_type == "continuous"
            else asset_to_image(self.asset).randomVisualizer()
        )

        self.preview_map.show_layer(
            masked_layer,
            "constraint",
            self.layer_name,
            self.aoi_model.feature_collection,
            base_layer,
        )

    @sd.catch_errors()
    def on_delete(self):
        """Remove the line from the model and trigger table update."""
        if self.layer_id in cp.mandatory_layers["constraint"]:
            raise Exception(cm.questionnaire.error.mandatory_layer)

        # Clean up the component before removing from model
        self.unobserve_all()

        # Now remove from the model
        self.model.remove(self.layer_id)

    def unobserve_all(self):
        """Remove all the observers."""
        try:
            self.w_maskout.unobserve(self.update_value, "v_model")
            self.aoi_model.unobserve(self.set_limits, "updated")
        except Exception as e:
            logger.debug(f"Error during unobserve: {e}")

        # Cancel the limits task
        if self._limits_task:
            self._limits_task.cancel()

    def update_value(self, *_):
        """Update the value of the model."""
        self.model.update_value(self.layer_id, self.w_maskout.v_model)
        self.get_model_data()

        # Real-time validation feedback
        is_valid, error_msg = self.validate_constraint_values()
        if not is_valid:
            # Set error state but don't disable widget (validation error)
            self.has_error = True
            self.error_message = error_msg
            self.error_type = "validation"
            logger.debug(f"Validation error for {self.layer_id}: {error_msg}")
        else:
            # Clear error state
            self.has_error = False
            self.error_message = ""
            self.error_type = ""

    def update_view(self):
        """Update the view when model data changes (called from table)."""
        # Refresh model data
        self.get_model_data()

        self.w_maskout.v_model = self.value

    def _set_limits_state(
        self,
        completed: bool,
        error: bool,
        error_message: str = "",
        error_type: str = "",
        loading: bool = False,
    ):
        """Helper method to set all limits-related state at once."""
        self.limits_completed = completed
        self.limits_error = error
        self.error_message = error_message
        self.error_type = error_type
        self.is_loading = loading
        self.has_error = error

    def _get_user_friendly_error(self, error_msg: str) -> str:
        """Convert technical error message to user-friendly message."""
        error_lower = error_msg.lower()

        # Check for access/permission errors
        if "not found" in error_lower and (
            "does not exist" in error_lower
            or "caller does not have access" in error_lower
        ):
            return f"The layer '{self.layer_name}' could not be accessed. Please verify the asset exists and you have permission to access it, or remove it from the questionnaire"
        elif (
            "permission" in error_lower
            or "access" in error_lower
            or "forbidden" in error_lower
        ):
            return f"The layer '{self.layer_name}' requires access permissions. Please check your Earth Engine permissions or remove it from the questionnaire"
        # Check for timeout errors
        elif "timeout" in error_lower or "timed out" in error_lower:
            return f"The layer '{self.layer_name}' couldn't be computed (timeout), please remove it from the questionnaire or try a new one"
        # Check for invalid data errors
        elif "invalid_argument" in error_lower or "invalid argument" in error_lower:
            return f"The layer '{self.layer_name}' couldn't be computed (invalid data), please remove it from the questionnaire or try a new one"
        # Generic error
        else:
            return f"The layer '{self.layer_name}' couldn't be computed, please remove it from the questionnaire or try a new one"

    def _create_limits_task(self):
        """Create the reusable limits task once."""

        def limits_callback(_):
            """Callback when limits are computed."""
            try:
                # Check if task has an error state before processing result
                if self._limits_task.state.value == "error":
                    limits_error_callback(self._limits_task)
                    return

                values = self._limits_task.result

                if self.data_type == "binary":
                    # Validate that all values are either 0 or 1 (subset of {0, 1})
                    if not all(val in [0, 1] for val in values):
                        raise Exception(
                            f"Binary asset must contain only 0 and/or 1 values, got {values}"
                        )
                    # Set default to the first available value
                    # Prefer masking out 0 if available (keeping 1s), otherwise mask out 1
                    default_maskout = 0 if 0 in values else 1
                    self.w_maskout.v_model = [default_maskout]

                elif self.data_type == "categorical":
                    if len(values) > 256:
                        raise Exception(
                            "Categorical asset must have less than 256 values"
                        )
                    values = get_categorical_values(self.asset, values)
                    self.w_maskout.items = values

                elif self.data_type == "continuous":
                    values = [int(val) for val in values]
                    self.w_maskout.widget.max_ = values[-1]
                    self.w_maskout.widget.min_ = values[0]

                    if not self.w_maskout.widget.v_model:
                        self.w_maskout.widget.v_model = [values[0], values[-1]]

                    if (values[-1] - values[0]) == 1:
                        self.w_maskout.widget.step = 0
                    else:
                        self.w_maskout.widget.step = 1

                self.update_value()
                self._set_limits_state(completed=True, error=False)

            except Exception as e:

                tb = traceback.format_exc()
                logger.error(f"Error setting limits for {self.layer_id}: {e}\n{tb}")

                # Check if this is a known validation error
                error_str = str(e)
                is_validation_error = (
                    "Binary asset must contain only" in error_str
                    or "Categorical asset must have less than" in error_str
                )

                if is_validation_error:
                    # For validation errors, include the exception message in error_msg
                    error_msg = f"The layer '{self.layer_name}' couldn't be computed: {error_str}"
                else:
                    # For other errors, use generic message with short traceback
                    short_tb_msg = get_short_traceback(tb)
                    error_msg = f"The layer '{self.layer_name}' couldn't be computed, please remove it from the questionnaire or try a new one. {short_tb_msg}"

                self._set_limits_state(
                    completed=False,
                    error=True,
                    error_message=error_msg,
                    error_type="computation",
                )

        def limits_error_callback(task):
            """Callback when limits computation fails."""

            # Extract error message from task
            error_msg = extract_task_error(task)
            logger.error(f"Failed to get limits for {self.layer_id}: {error_msg}")

            # Convert to user-friendly message
            user_msg = self._get_user_friendly_error(error_msg)

            self._set_limits_state(
                completed=False,
                error=True,
                error_message=user_msg,
                error_type="computation",
            )

        def limits_finally_callback():
            """Callback that always runs after limits computation."""
            # Check if we're in an error state but the error callback wasn't triggered
            if self._limits_task.state.value == "error" and not self.limits_error:
                limits_error_callback(self._limits_task)

            self.is_loading = False
            self.w_maskout.set_loading(False)

            # Perform validation after loading completes (only if no computation error)
            if not self.limits_error:
                self.validate_current_values()

        # Create the task once
        self._limits_task = self.gee_interface.create_task(
            func=gee.get_limits_async,
            key=f"constraint_limits_{self.layer_id}",
            on_done=limits_callback,
            on_error=limits_error_callback,
            on_finally=limits_finally_callback,
        )
        logger.debug(f"Created limits task for {self.layer_id}")

    @sd.need_ee
    def set_limits(self, *_) -> None:
        """Get the min and max value of the asset in the aoi using the reusable task."""
        logger.debug(f"set_limits called for {self.layer_id}")
        self.aoi = self.aoi_model.feature_collection

        # if there's no AOI we'll assume we are in the default constraint
        if not self.aoi:
            logger.debug(f"No AOI for {self.layer_id}, using default values")
            self.w_maskout.v_model = [0]
            self.update_value()
            self._set_limits_state(completed=True, error=False)
            return

        # before updating the limits, check if this layer is in the model
        if self.layer_id not in self.model.ids:
            logger.debug(f"Layer {self.layer_id} not in model, skipping")
            self._set_limits_state(completed=True, error=False)
            return

        logger.debug(f"Starting limits task for {self.layer_id}")

        # Cancel any existing task execution
        if self._limits_task:
            self._limits_task.cancel()

        # Clear error state and set loading state
        self._set_limits_state(completed=False, error=False, loading=True)

        # Start the task with current parameters
        self._limits_task.start(
            self.gee_interface, self.asset, self.data_type, self.aoi
        )

    @property
    def is_ready(self) -> bool:
        """Check if the constraint row has completed loading its limits."""
        return self.limits_completed and not self.is_loading and not self.limits_error

    @property
    def is_loading_state(self) -> bool:
        """Check if the constraint row is currently loading limits."""
        return self.is_loading

    @property
    def has_error_state(self) -> bool:
        """Check if the constraint row has an error."""
        return self.has_error or self.limits_error
