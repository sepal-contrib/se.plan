"""Dialog to display and handle invalid constraints found during recipe loading."""

import ipyvuetify as v
import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts.decorator import switch
from typing import List, Callable

from component.message import cm

import logging

logger = logging.getLogger("SEPLAN")


class InvalidConstraintsDialog(v.Dialog):
    """Dialog that displays invalid constraints and offers to fix the recipe."""

    def __init__(self, on_fix_callback: Callable = None, **kwargs):
        """
        Initialize the invalid constraints dialog.

        Args:
            on_fix_callback: Function to call when user chooses to fix the recipe.
                            Should accept no arguments and handle the save operation.
        """
        self.on_fix_callback = on_fix_callback

        # Create the alert for user feedback
        self.alert = sw.Alert()

        # Create the list to display invalid constraints
        self.constraint_list = v.Html(tag="div", children=[])

        # Create action buttons
        self.btn_fix = sw.Btn(
            "Fix and Save Recipe", color="warning", outlined=True, class_="ma-2"
        )
        self.btn_cancel = sw.Btn(
            "Continue without Fixing", color="primary", outlined=True, class_="ma-2"
        )

        # Wire up events
        self.btn_fix.on_event("click", self._on_fix_click)
        self.btn_cancel.on_event("click", self._on_cancel_click)

        # Create dialog content
        content = v.Card(
            class_="pa-4",
            children=[
                v.CardTitle(
                    children=[
                        v.Icon(children=["mdi-alert"], color="warning", class_="mr-2"),
                        "Invalid Constraints Detected",
                    ],
                    class_="text-h5",
                ),
                v.CardText(
                    children=[
                        v.Html(
                            tag="p",
                            class_="mb-4",
                            children=[
                                "The following constraints have invalid data and were automatically "
                                "removed from the loaded recipe. The recipe will work with the remaining "
                                "valid constraints."
                            ],
                        ),
                        v.Html(
                            tag="p",
                            class_="mb-2 font-weight-bold",
                            children=["Invalid constraints:"],
                        ),
                        self.constraint_list,
                        v.Divider(class_="my-4"),
                        v.Html(
                            tag="p",
                            class_="mb-2",
                            children=[
                                "You can continue working with the current recipe, or fix the recipe "
                                "file by removing these invalid constraints permanently."
                            ],
                        ),
                        self.alert,
                    ]
                ),
                v.CardActions(
                    children=[
                        v.Spacer(),
                        self.btn_cancel,
                        self.btn_fix,
                    ]
                ),
            ],
        )

        # Initialize dialog
        super().__init__(
            v_model=False, max_width=700, persistent=True, children=[content], **kwargs
        )

    def show(self, invalid_constraints: List[dict]):
        """
        Display the dialog with the list of invalid constraints.

        Args:
            invalid_constraints: List of dicts, each containing:
                - name: Constraint name
                - data_type: Expected data type
                - values: Invalid values
                - error: Error message
        """
        if not invalid_constraints:
            return

        # Build the list of invalid constraints
        constraint_items = []

        for constraint in invalid_constraints:
            name = constraint.get("name", "Unknown")
            data_type = constraint.get("data_type", "unknown")
            values = constraint.get("values", [])
            error = constraint.get("error", "Unknown error")

            # Create a formatted entry for this constraint
            item = v.Html(
                tag="div",
                class_="mb-3 pa-3 grey lighten-4 rounded",
                children=[
                    v.Html(
                        tag="div",
                        class_="font-weight-bold text-body-1",
                        children=[f"• {name}"],
                    ),
                    v.Html(
                        tag="div",
                        class_="ml-4 text-body-2",
                        children=[
                            f"Type: {data_type}, Values: {values}",
                            v.Html(tag="br"),
                            v.Html(
                                tag="span",
                                class_="error--text",
                                children=[f"Error: {error}"],
                            ),
                        ],
                    ),
                ],
            )
            constraint_items.append(item)

        self.constraint_list.children = constraint_items

        # Reset alert
        self.alert.reset()

        # Show the dialog
        self.v_model = True

        logger.info(
            f"Showing invalid constraints dialog with {len(invalid_constraints)} items"
        )

    @switch("loading", "disabled", on_widgets=["btn_fix", "btn_cancel"])
    def _on_fix_click(self, *args):
        """Handle fix button click - save recipe without invalid constraints."""
        self.alert.reset()

        try:
            if self.on_fix_callback:
                self.on_fix_callback()
                self.alert.add_msg(
                    "Recipe fixed successfully! Invalid constraints have been removed.",
                    "success",
                )
                # Close dialog after short delay
                import time

                time.sleep(1)
                self.v_model = False
            else:
                logger.error("No fix callback provided")
                self.alert.add_msg(
                    "Error: Unable to fix recipe (no callback configured)", "error"
                )

        except Exception as e:
            logger.exception(f"Error fixing recipe: {e}")
            self.alert.add_msg(f"Error fixing recipe: {str(e)}", "error")

    def _on_cancel_click(self, *args):
        """Handle cancel button click - close dialog without fixing."""
        self.v_model = False
        logger.info("User cancelled invalid constraints fix")
