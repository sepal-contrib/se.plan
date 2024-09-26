from typing import Union

import pandas as pd
from sepal_ui import sepalwidgets as sw

from component import parameter as cp
from component.message import cm
from component.model.benefit_model import BenefitModel
from component.model.constraint_model import ConstraintModel
from component.model.cost_model import CostModel
from component.scripts.plots import get_bars_chart
from component.scripts.statistics import parse_layer_data
from component.types import SummaryStatsDict


# taken from https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python
def human_format(num, round_to=2):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)

    prefix = ["", "k", "M", "B", "T"][magnitude]

    return "{:.{}f}{}".format(num, round_to, prefix)


class LayerFull(sw.Layout):
    model: Union[BenefitModel, CostModel]
    "Questionnaire model used to retrieve the layer name, description and units"

    def __init__(
        self,
        summary_stats: SummaryStatsDict,
        layer_id: str,
        model: Union[BenefitModel, CostModel],
    ):

        # We need to get the labels from the seplan models
        layer_idx = model.get_index(layer_id)
        detail = model.descs[layer_idx]
        name = model.names[layer_idx]
        units = model.units[layer_idx]

        # build the internal details
        w_header = sw.ExpansionPanelHeader(
            children=[cm.dashboard.theme.benefit.details],
            expand_icon="mdi-help-circle-outline",
            disable_icon_rotate=True,
        )
        w_content = sw.ExpansionPanelContent(children=[detail])
        w_panel = sw.ExpansionPanel(children=[w_header, w_content])
        w_details = sw.ExpansionPanels(xs12=True, class_="mt-3", children=[w_panel])

        # create a title with the layer name
        label = f"{name} ({units})"
        w_title = sw.Html(class_="mt-2 mb-2", xs12=True, tag="h3", children=[label])

        # create the chart
        aoi_names, values, colors = parse_layer_data(summary_stats, layer_id)
        w_chart = get_bars_chart(aoi_names, values, colors)

        # build the final widget
        widgets = [w_title, w_chart, w_details]
        children = [sw.Flex(xs12=True, children=[w]) for w in widgets]
        super().__init__(class_="ma-5", row=True, children=children)


class LayerPercentage(sw.Layout):
    model: ConstraintModel
    "Questionnaire model used to retrieve the layer name, description and units"

    def __init__(self, layer_id, pcts, names_colors, model: ConstraintModel):
        self.model = model
        # add one extra color for the AOI
        colors = [color for _, color in names_colors]

        # We need to get the labels from the seplan models
        layer_idx = self.model.get_index(layer_id)
        detail = self.model.descs[layer_idx]
        name = self.model.names[layer_idx]

        # deal with land_use special case
        if layer_id in [*cp.land_use_criterias]:
            columns = [
                "theme",
                "subtheme",
                "layer_name",
                "gee_asset",
                "layer_info",
                "unit",
            ]
            content = ["", "", layer_id, "", layer_id, "HA"]
            pd.Series(dict(zip(columns, content)))

        # add the title
        w_title = sw.Html(tag="h4", children=[name])

        # build the internal expantionpanel
        w_header = sw.ExpansionPanelHeader(
            children=[cm.dashboard.theme.benefit.details],
            expand_icon="mdi-help-circle-outline",
            disable_icon_rotate=True,
        )
        w_content = sw.ExpansionPanelContent(children=[detail])
        w_panel = sw.ExpansionPanel(children=[w_header, w_content])
        w_details = sw.ExpansionPanels(xs12=True, class_="mt-3", children=[w_panel])

        # create the list of value
        spans = []
        for i, val in enumerate(pcts):
            c = f"color: {colors[i]}"
            val = f"{round(val,2)}%"
            w_span = sw.Html(tag="span", class_="ml-1 mr-1", style_=c, children=[val])
            spans.append(w_span)

        # assemble everything
        widgets = [[w_title] + spans, [w_details]]
        children = [sw.Flex(xs12=True, children=w) for w in widgets]
        super().__init__(class_="ma-5", row=True, children=children)

        # hide the constraints if all values are 0
        self.viz = any([v != 0 for v in pcts])
