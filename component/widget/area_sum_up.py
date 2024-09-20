import ipyvuetify as v
from ipywidgets import Output
from matplotlib import pyplot as plt

from component import parameter as cp
from component.message import cm
from component.parameter.gui_params import SUITABILITY_LEVELS
from component.parameter.vis_params import SUITABILITY_COLORS


class AreaSumUp(v.Layout):

    def __init__(self, title, surfaces=[0] * 6):
        # get the total surface for ratio
        total_surface = sum(surfaces)

        # normalize surfaces
        norm_surfaces = [(s / total_surface) * 100 for s in surfaces]

        # create a matplotlib stack horizontal bar chart
        chart = Output()
        with chart:
            # create the chart
            fig, ax = plt.subplots(figsize=[50, 2], facecolor=((0, 0, 0, 0)))

            # add the axis
            for i, surface in enumerate(norm_surfaces):
                ax.barh(
                    title,
                    surface,
                    left=sum(norm_surfaces[:i]),
                    color=SUITABILITY_COLORS[i + 1],
                )

            # cosmetic tuning
            ax.set_xlim(0, 100)
            ax.set_axis_off()

            plt.show()


def get_summary_table(summary_stats):

    # init the table
    headers = [
        v.Html(tag="th", children=[SUITABILITY_LEVELS[0]]),
        v.Html(tag="th", class_="text-right", children=[SUITABILITY_LEVELS[1]]),
        v.Html(tag="th", class_="text-right", children=[SUITABILITY_LEVELS[2]]),
    ]
    row = v.Html(tag="tr", children=headers)
    w_header = [v.Html(tag="thead", children=[row])]

    rows = []
    params = enumerate(zip(surfaces, norm_surfaces), 1)
    for i, (val, norm) in params:
        tds = [
            v.Html(
                tag="td",
                children=[SUITABILITY_LEVELS[i]],
                style_=f"color: {SUITABILITY_COLORS[i]}",
            ),
            v.Html(tag="td", class_="text-right", children=[f"{float(val):,.1f}"]),
            v.Html(tag="td", class_="text-right", children=[f"{float(norm):,.1f}"]),
        ]
        row = v.Html(tag="tr", children=tds)

        rows.append(row)

    w_body = [v.Html(tag="tbody", children=rows)]
    table = v.SimpleTable(small=True, xs12=True, children=w_header + w_body)

    # the table should not be displayed by default but as a detail expansion panel
    header = v.ExpansionPanelHeader(children=[cm.dashboard.region.detail])
    content = v.ExpansionPanelContent(children=[table])
    panel = v.ExpansionPanel(children=[header, content])
    ep = v.ExpansionPanels(children=[panel])

    # init the title
    title = v.Html(xs12=True, class_="mb-2", tag="h2", children=[title])

    # create the widget
    super().__init__(
        row=True,
        class_="ma-5",
        children=[
            v.Flex(xs12=True, children=[title]),
            v.Flex(xs12=True, children=[chart]),
            v.Flex(xs12=True, children=[ep]),
        ],
    )
