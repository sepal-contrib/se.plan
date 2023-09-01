import random
import string
from typing import List, Literal

import sepal_ui.sepalwidgets as sw
from ipyleaflet import WidgetControl

from component.message import cm


def SuitabilityLegend() -> WidgetControl:
    """Create a legend for the map.

    Colors of the table will come from a css simple file located in fronted.
    """
    id_ = "".join(random.choices(string.ascii_letters, k=5))

    style = sw.Html(
        tag="style",
        children=[
            f"""
            .legend_{id_} {{
                height: 25px;
                background-color: #353535;
                background-image:
                    linear-gradient(
                    to right, 
                    #353535,
                    #353535 16.66%,
                    #edf8fb 16.66%,
                    #66c2a4,
                    #006d2c
                    );
            }}

            .td_title_{id_} {{
                text-align:center !important;
                font-size: 14px !important;
                height: auto !important;
            }}
            .td_legend_{id_} {{
                padding: 0px !important;
                height: auto !important;
            }}

            .td_label_{id_} {{
                width: 16.66%;
                font-size: 12px !important;
                line-height: 18px !important;
                text-align:center !important;
                height: auto !important;
            }}
            """
        ],
    )

    title = sw.Html(
        tag="td",
        class_=f"td_title_{id_}",
        attributes={"colspan": 6},
        children=[sw.Html(tag="div", children="Restoration suitability index")],
    )

    legend_bar = sw.Html(
        tag="td",
        class_=f"td_legend_{id_}",
        attributes={"colspan": 6},
        children=[sw.Html(tag="div", class_=f"legend_{id_}")],
    )

    legend_names = {
        "nodata": cm.map.legend.class_.nodata,
        "vlow": cm.map.legend.class_.vlow,
        "low": cm.map.legend.class_.low,
        "medium": cm.map.legend.class_.medium,
        "high": cm.map.legend.class_.high,
        "vhigh": cm.map.legend.class_.vhigh,
    }

    legend_label = [
        sw.Html(tag="td", class_=f"td_label_{id_}", children=[name])
        for name in legend_names.values()
    ]

    legend = sw.SimpleTable(
        style_="width:450px; background-color: transparent;",
        class_="pa-0 ma-0",
        children=[
            style,
            sw.Html(tag="tr", children=[title]),
            sw.Html(tag="tr", children=[legend_bar]),
            sw.Html(tag="tr", children=legend_label),
        ],
    )
    # return legend

    return WidgetControl(
        widget=legend,
        position="bottomright",
        transparent_bg=True,
    )


class Legend(WidgetControl):
    def __init__(
        self,
        type_: Literal["stepped", "gradient"] = None,
        title: str = None,
        names: List[str] = None,
        colors: List[str] = None,
    ):
        """Create a legend for the map.

        Args:
            type_ (str): Type of the legend. Can be "stepped" or "gradient".
            title (str): Title of the legend.
            colors (list): Dictionary of colors.
            names (list): List of names for the legend.
        """
        # create a random name for the legend
        # this is needed to avoid having the same legend for different layers
        self.id_ = "".join(random.choices(string.ascii_letters, k=5))

        self.title_row = sw.Html(tag="tr")
        self.color_row = sw.Html(tag="tr")
        self.label_row = sw.Html(tag="tr", class_=f"legend_tr_{self.id_}")

        self.style = sw.Html(tag="style")

        legend = sw.SimpleTable(
            style_="width:450px; background-color: transparent;",
            class_="pa-0 ma-0",
            children=[self.style, self.title_row, self.color_row, self.label_row],
        )

        control_args = {}
        control_args["widget"] = legend
        control_args["position"] = "bottomright"
        control_args["transparent_bg"] = True
        control_args["attributes"] = {"id": "legend"}

        super().__init__(**control_args)

        if all([type_, title, names, colors]):
            self.update_legend(type_, title, names, colors)

    def update_legend(
        self,
        type_: Literal["stepped", "gradient"],
        title: str,
        names: List[str],
        colors: List[str],
    ):
        names = [str(name) for name in names]
        gradient = get_color_css(type_, colors)

        style = f"""
            .legend_{self.id_} {{
                height: 20px;
                background-color: #353535;
                {gradient}
            }}

            .td_title_{self.id_} {{
                text-align:center !important;
                font-size: 14px !important;
                height: auto !important;
            }}

            .td_legend_{self.id_} {{
                padding: 0px !important;
                height: auto !important;
            }}

            .td_label_{self.id_} {{
                width: {100/len(names)}%;
                font-size: 12px !important;
                line-height: 18px !important;
                text-align:center !important;
                height: auto !important;
                padding: 0px !important;
            }}
           
        """

        if len(names) <= 3:
            style += f"""
            .legend_tr_{self.id_} > td:first-child {{
                text-align: left !important;
            }}

            .legend_tr_{self.id_} > td:last-child {{
                text-align: right !important;
            }}
            """

        self.title_row.children = [
            sw.Html(
                tag="td",
                class_=f"td_title_{self.id_}",
                attributes={"colspan": len(names)},
                children=[sw.Html(tag="div", children=title)],
            )
        ]

        self.color_row.children = [
            sw.Html(
                tag="td",
                class_=f"td_legend_{self.id_}",
                attributes={"colspan": len(names)},
                children=[sw.Html(tag="div", class_=f"legend_{self.id_}")],
            )
        ]

        self.label_row.children = [
            sw.Html(tag="td", class_=f"td_label_{self.id_}", children=[name])
            for name in names
        ]

        self.style.children = [style]


def get_color_css(type_, colors):
    """Generates a CSS linear-gradient from a list of colors.

    Parameters:
    - colors: list of strings representing CSS colors.

    Returns:
    - CSS string with linear-gradient.
    """
    if type_ == "gradient":
        return f"background: linear-gradient(to right, {', '.join(colors)})"

    if not colors:
        return ""

    if len(colors) == 1:
        return f"background: {colors[0]};"

    num_colors = len(colors)
    percentage = 100 / num_colors

    segments = []
    for i, color in enumerate(colors):
        start = i * percentage
        end = (i + 1) * percentage
        if i == num_colors - 1:  # For the d color
            segments.append(f"{color} {start:.2f}%")
        else:
            segments.append(f"{color} {start:.2f}% {end:.2f}%")

    gradient = ", ".join(segments)
    css = f"background: linear-gradient(to right, {gradient});"

    return css
