import ipyvuetify as v
from ipywidgets import Output
from matplotlib import pyplot as plt

from component import parameter as cp
from component.message import cm
from component import scripts as cs

class CarbonSumUp(v.Layout):

    NAMES = ["restoration potential", "Carbon sequestered after 40 years(tonnes C)", "ratio over total carbon sequestered (%)"]#todo: move to something like- cm.dashboard.region.names
    COLORS = cp.gradient(5) + cp.no_data_color
    POTENTIALS = cm.dashboard.region.potentials

    def __init__(self, title, surfaces=[0] * 6):
        # get the total surface for ratio
        total_surface = sum(surfaces)

        # normalize surfaces
        norm_surfaces = [(s / total_surface) * 100 for s in surfaces]

#         # create a matplotlib stack horizontal bar chart
#         chart = Output()
#         with chart:

#             # create the chart
#             fig, ax = plt.subplots(figsize=[50, 2], facecolor=((0, 0, 0, 0)))

#             # add the axis
#             for i, surface in enumerate(norm_surfaces):
#                 ax.barh(
#                     title, surface, left=sum(norm_surfaces[:i]), color=self.COLORS[i]
#                 )

#             # cosmetic tuning
#             ax.set_xlim(0, 100)
#             ax.set_axis_off()

#             plt.show()

        # init the table
        heads = [v.Html(tag="th", children=[name]) for name in self.NAMES]
        row = v.Html(tag="tr", children=heads)
        w_header = [v.Html(tag="thead", children=[row])]

        self.rows = []
        params = zip(self.COLORS, self.POTENTIALS, surfaces, norm_surfaces)
        for clr, ptl, val, norm in params:

            tds = [
                v.Html(tag="td", children=[ptl], style_=f"color: {clr}"),
                v.Html(tag="td", children=[f"{float(val):.1f}"]),
                v.Html(tag="td", children=[f"{float(norm):.1f}"]),
            ]
            row = v.Html(tag="tr", children=tds)

            self.rows.append(row)

        w_body = [v.Html(tag="tbody", children=self.rows)]
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
                # v.Flex(xs12=True, children=[chart]),
                v.Flex(xs12=True, children=[ep]),
            ],
        )
