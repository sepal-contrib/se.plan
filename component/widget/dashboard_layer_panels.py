from typing import List
from ipecharts import EChartsWidget

from sepal_ui import sepalwidgets as sw
from sepal_ui.frontend.resize_trigger import rt

from component.message import cm
from component.types import ConstraintLayerData, ModelLayerData


# taken from https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python
def human_format(num, round_to=2):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)

    prefix = ["", "k", "M", "B", "T"][magnitude]

    return "{:.{}f}{}".format(num, round_to, prefix)


class LayerFull(sw.Layout):

    def __init__(self, layer_data: ModelLayerData, charts: List[EChartsWidget]):

        # get the layer data
        name = layer_data["name"]
        detail = layer_data["desc"]
        units = layer_data["unit"]

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

        # build the final widget
        widgets = [w_title] + charts + [w_details]
        children = [sw.Flex(xs12=True, children=[w]) for w in widgets]
        super().__init__(class_="ma-5", row=True, children=children)


class LayerPercentage(sw.Layout):

    def __init__(
        self,
        layer_data: ModelLayerData,
        values: List[List[float]],
        colors: List[List[str]],
    ):
        print("*********", colors, values)

        detail = layer_data.get("desc")
        name = layer_data.get("name")

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

        rows = []
        for i, i_val in enumerate(values):
            spans = []
            for j, j_val in enumerate(i_val):
                c = f"color: {colors[i][j]}"
                round_val = f"{round(j_val,2)}%"
                w_span = sw.Html(
                    tag="span", class_="ml-1 mr-1", style_=c, children=[round_val]
                )
                spans.append(w_span)

            rows.append(sw.Row(xs12=True, children=spans))

        # assemble everything
        widgets = [[w_title] + rows, [w_details]]
        children = [sw.Flex(xs12=True, children=w) for w in widgets]
        super().__init__(class_="ma-5", row=True, children=children)

        # hide the constraints if all values are 0
        self.viz = any([v != 0 for v in values])
