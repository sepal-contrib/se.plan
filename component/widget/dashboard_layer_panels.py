from ipecharts import EChartsWidget

from sepal_ui import sepalwidgets as sw
from sepal_ui.frontend.resize_trigger import rt

from component.message import cm
from component.types import ModelLayerData


# taken from https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python
def human_format(num, round_to=2):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)

    prefix = ["", "k", "M", "B", "T"][magnitude]

    return "{:.{}f}{}".format(num, round_to, prefix)


class LayerFull(sw.Layout):

    def __init__(self, layer_data: ModelLayerData, w_chart: EChartsWidget):

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

        # create the chart

        # build the final widget
        widgets = [w_title, w_chart, w_details]
        children = [sw.Flex(xs12=True, children=[w]) for w in widgets]
        super().__init__(class_="ma-5", row=True, children=children)


class LayerPercentage(sw.Layout):

    def __init__(self, layer_data, values, colors):

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

        # create the list of value
        spans = []
        for i, val in enumerate(values):
            c = f"color: {colors[i]}"
            val = f"{round(val,2)}%"
            w_span = sw.Html(tag="span", class_="ml-1 mr-1", style_=c, children=[val])
            spans.append(w_span)

        # assemble everything
        widgets = [[w_title] + spans, [w_details]]
        children = [sw.Flex(xs12=True, children=w) for w in widgets]
        super().__init__(class_="ma-5", row=True, children=children)

        # hide the constraints if all values are 0
        self.viz = any([v != 0 for v in values])
