from typing import List, Union
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

    def __init__(
        self,
        layer_data: Union[ModelLayerData, List[ModelLayerData]],
        charts: List[EChartsWidget],
        recipe_names: List[str] = [],
    ):

        # For the case of multiple data layers I want to display all the info in the single panel
        # This happens with the cost layer, where we want to display all them together

        if isinstance(layer_data, list):
            # concatenate all the data
            name = ", ".join([l["name"] for l in layer_data])
            detail = ", <br><br>".join([l["desc"] for l in layer_data])
            units = ", ".join([l["unit"] for l in layer_data])

        else:
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
        w_content = sw.ExpansionPanelContent(children=[sw.Markdown(detail)])
        w_panel = sw.ExpansionPanel(children=[w_header, w_content])
        w_details = sw.ExpansionPanels(xs12=True, class_="mt-3", children=[w_panel])

        # create a title with the layer name
        label = f"{name} ({units})"

        w_title = sw.Html(
            class_="mt-2 mb-2",
            xs12=True,
            tag="h2",
            children=[label],
            style_="text-align: center;",
        )

        # If there's more than one chart, I want to display them in a row and with a title
        if len(charts) > 1:
            charts = [
                sw.Flex(
                    xs12=True,
                    children=[
                        sw.Html(tag="h4", children=["Recipe: ", recipe_name]),
                        chart,
                    ],
                )
                for chart, recipe_name in zip(charts, recipe_names)
            ]

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
