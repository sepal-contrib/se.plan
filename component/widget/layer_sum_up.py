from sepal_ui import color as scolor
from sepal_ui import sepalwidgets as sw
import pandas as pd
from ipywidgets import Output
from matplotlib import pyplot as plt

from component import parameter as cp
from component.message import cm


class LayerFull(sw.Layout):

    COLORS = cp.gradient(5) + ["grey"]

    def __init__(self, layer_name, values, aoi_names, colors):

        # get the layer labels from the translator object
        t_layer = getattr(cm.layers, layer_name)

        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna("")
        layer_row = layer_list[layer_list.layer_id == layer_name]

        # build the internal details
        details = sw.ExpansionPanels(
            xs12=True,
            class_="mt-3",
            children=[
                sw.ExpansionPanel(
                    children=[
                        sw.ExpansionPanelHeader(
                            children=[cm.dashboard.theme.benefit.details],
                            expand_icon="mdi-help-circle-outline",
                            disable_icon_rotate=True,
                        ),
                        sw.ExpansionPanelContent(children=[t_layer.detail]),
                    ]
                )
            ],
        )

        # create a title with the layer name
        title = sw.Html(
            class_="mt-2 mb-2",
            xs12=True,
            tag="h3",
            children=[f"{t_layer.name} ({layer_row.unit.values[0]})"],
        )

        # taken from https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python
        def human_format(num, round_to=2):
            magnitude = 0
            while abs(num) >= 1000:
                magnitude += 1
                num = round(num / 1000.0, round_to)
            return "{:.{}f}{}".format(
                round(num, round_to), round_to, ["", "k", "M", "G", "T", "P"][magnitude]
            )

        # create a matplotlib stack horizontal bar chart
        chart = Output()
        with chart:

            # change pyplot style
            plt.style.use("dark_background")

            # create the chart
            fig, ax = plt.subplots(
                figsize=[50, len(values) * 2], facecolor=((0, 0, 0, 0))
            )

            # set the datas
            max_value = max(values)
            norm_values = [v / max_value * 100 for v in reversed(values)]
            human_values = [f"{human_format(val)}" for val in reversed(values)]
            colors = [
                colors[i - 1] if i else scolor.primary for i in range(len(values))
            ][::-1]

            # add the axes
            ax.barh(aoi_names, norm_values, color=colors)

            # add the text
            for i, (norm, name, val, color) in enumerate(
                zip(norm_values, aoi_names, human_values, colors)
            ):
                ax.text(norm + 1, i, val, fontsize=40, color=color)

            # cosmetic tuning
            ax.set_xlim(0, 110)
            ax.tick_params(axis="y", which="major", pad=30, labelsize=40, left=False)
            ax.tick_params(axis="x", bottom=False, labelbottom=False)
            ax.set_frame_on(False)

            plt.show()

        super().__init__(
            class_="ma-5",
            row=True,
            children=[
                sw.Flex(xs12=True, children=[title]),
                sw.Flex(xs12=True, children=[chart]),
                sw.Flex(xs12=True, children=[details]),
            ],
        )


class LayerPercentage(sw.Layout):
    def __init__(self, layer_name, pcts, colors):

        # get the layer labels from the translator object
        t_layer = getattr(cm.layers, layer_name)

        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna("")
        layer_row = layer_list[layer_list.layer_id == layer_name]

        if len(layer_row) != 1 and layer_name not in cp.criterias:
            raise IndexError(
                f"The layer {t_layer.name} is not part of the existing layers of the application. Please contact our maintainer."
            )

        # deal with land_use special case
        if len(layer_row) != 1 and layer_name in cp.criterias:
            layer_row = pd.DataFrame(
                [["", "", layer_name, "", layer_name, "HA"]],
                columns=[
                    "theme",
                    "subtheme",
                    "layer_name",
                    "gee_asset",
                    "layer_info",
                    "unit",
                ],
            )

        # add the title
        title = sw.Html(tag="h4", children=[t_layer.name])
        # build the internal details
        details = sw.ExpansionPanels(
            xs12=True,
            class_="mt-3",
            children=[
                sw.ExpansionPanel(
                    children=[
                        sw.ExpansionPanelHeader(
                            children=[cm.dashboard.theme.benefit.details],
                            expand_icon="mdi-help-circle-outline",
                            disable_icon_rotate=True,
                        ),
                        sw.ExpansionPanelContent(children=[t_layer.detail]),
                    ]
                )
            ],
        )

        # create the list of value
        spans = []
        for i, val in enumerate(pcts):
            # if val != 0: #TODO: do we need this still?
            spans.append(
                sw.Html(
                    tag="span",
                    class_="ml-1 mr-1",
                    style_=f"color: {colors[i-1] if i else scolor.primary}",
                    children=[f"{round(val,2)}%"],
                )
            )

        super().__init__(
            class_="ma-5",
            row=True,
            children=[
                sw.Flex(xs12=True, children=[title] + spans),
                sw.Flex(xs12=True, children=[details]),
            ],
        )

        # hide the constraints if all values are 0
        self.viz = any([v != 0 for v in pcts])
