from typing import Literal
import ee
import ipyvuetify as v
from component.scripts.seplan import Seplan, reduce_constraints
from component.widget.buttons import IconBtn
from component.widget.preview_map_dialog import PreviewMapDialog
from component.widget.alert_state import Alert
from sepal_ui.scripts import decorator as sd


class PreviewThemeBtn(v.Flex):
    def __init__(
        self,
        type_: Literal["benefit", "constraint", "cost"],
        map_: PreviewMapDialog,
        seplan: Seplan,
        alert: Alert,
    ):

        # to align the flex container to the right
        self.style_ = "flex: 0"

        super().__init__()

        self.type_ = type_
        self.map_ = map_ or PreviewMapDialog()
        self.seplan = seplan
        self.alert = alert or Alert()

        self.color = "primary"
        self.btn = IconBtn("mdi-map")
        self.children = [self.btn]

        self.btn.on_event("click", self.load_layer)

    @sd.catch_errors()
    def load_layer(self, *_):
        """Load the layer on the map."""

        if self.type_ == "benefit":
            layer = self.seplan.get_benefit_index()
            name = "Benefit"

        elif self.type_ == "constraint":

            layer = reduce_constraints(self.seplan.get_masked_constraints_list())
            name = "Constraint"

        elif self.type_ == "cost":

            layer = ee.Image(
                [image for image, _ in self.seplan.get_costs_list()]
            ).reduce(ee.Reducer.sum())
            name = "Cost"

        self.map_.show_layer(
            layer, self.type_, name, self.seplan.aoi_model.feature_collection
        )
