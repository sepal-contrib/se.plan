from sepal_ui import color as scolor
from sepal_ui import sepalwidgets as sw
import pandas as pd
from ipywidgets import Output
from matplotlib import pyplot as plt

from component import parameter as cp
from component.message import cm

# taken from https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python
def human_format(num, round_to=2):

    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)

    prefix = ["", "k", "M", "G", "T", "P"][magnitude]

    return "{:.{}f}{}".format(num, round_to, prefix)


class LayerFull(sw.Layout):
    def __init__(self, layer_id, values, aoi_names, colors):

        # add one extra color for the AOI
        colors = [c for c in reversed([scolor.primary] + colors)]

        # get the layer labels from the translator object
        t_layer = getattr(cm.layers, layer_id)

        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna("")
        layer_row = layer_list[layer_list.layer_id == layer_id].squeeze()

        # build the internal details
        w_header = sw.ExpansionPanelHeader(
            children=[cm.dashboard.theme.benefit.details],
            expand_icon="mdi-help-circle-outline",
            disable_icon_rotate=True,
        )
        w_content = sw.ExpansionPanelContent(children=[t_layer.detail])
        w_panel = sw.ExpansionPanel(children=[w_header, w_content])
        w_details = sw.ExpansionPanels(xs12=True, class_="mt-3", children=[w_panel])

        # create a title with the layer name
        label = f"{t_layer.name} ({layer_row.unit})"
        w_title = sw.Html(class_="mt-2 mb-2", xs12=True, tag="h3", children=[label])

        # create a matplotlib stack horizontal bar chart
        w_chart = Output()
        with w_chart:

            # change pyplot style
            plt.style.use("dark_background")

            # create the chart
            transparent = (0, 0, 0, 0)
            width = len(values) * 2
            fig, ax = plt.subplots(figsize=[50, width], facecolor=transparent)

            # set the datas
            max_value = max(values) if max(values) != 0 else 1
            norm_values = [v / max_value * 100 for v in reversed(values)]
            human_values = [f"{human_format(val)}" for val in reversed(values)]

            # add the axes
            ax.barh(aoi_names, norm_values, color=colors)

            # add the text
            info = (norm_values, human_values, colors)
            for i, (norm, val, color) in enumerate(zip(*info)):
                ax.text(norm + 1, i, val, fontsize=40, color=color)

            # cosmetic tuning
            ax.set_xlim(0, 110)
            ax.tick_params(axis="y", which="major", pad=30, labelsize=40, left=False)
            ax.tick_params(axis="x", bottom=False, labelbottom=False)
            ax.set_frame_on(False)

            plt.show()

        # build the final widget
        widgets = [w_title, w_chart, w_details]
        children = [sw.Flex(xs12=True, children=[w]) for w in widgets]
        super().__init__(class_="ma-5", row=True, children=children)


class LayerPercentage(sw.Layout):
    def __init__(self, layer_id, pcts, colors):

        # add one extra color for the AOI
        colors = [scolor.primary] + colors

        # get the layer labels from the translator object
        t_layer = getattr(cm.layers, layer_id)

        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna("")
        layer_row = layer_list[layer_list.layer_id == layer_id].squeeze()

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
            layer_row = pd.Series(dict(zip(columns, content)))

        # add the title
        w_title = sw.Html(tag="h4", children=[t_layer.name])

        # build the internal expantionpanel
        w_header = sw.ExpansionPanelHeader(
            children=[cm.dashboard.theme.benefit.details],
            expand_icon="mdi-help-circle-outline",
            disable_icon_rotate=True,
        )
        w_content = sw.ExpansionPanelContent(children=[t_layer.detail])
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
