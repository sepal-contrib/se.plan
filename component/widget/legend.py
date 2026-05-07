import random
import string
from typing import List, Literal

import sepal_ui.sepalwidgets as sw
from ipyleaflet import WidgetControl


class Legend(WidgetControl):
    """Map legend widget styled to match the pysepal Solara legend overlay.

    Kept as an ipyleaflet ``WidgetControl`` (rather than the Solara
    ``LegendComponent``) because this legend lives inside dialog-bound maps
    (e.g. ``PreviewMapDialog``) where a body-fixed Solara overlay would
    render outside the dialog.
    """

    def __init__(
        self,
        type_: Literal["stepped", "gradient"] = None,
        title: str = None,
        names: List[str] = None,
        colors: List[str] = None,
    ):
        self.id_ = "".join(random.choices(string.ascii_letters, k=5))

        self.title_div = sw.Html(tag="div", class_=f"seplan-legend__title_{self.id_}")
        self.bar_div = sw.Html(tag="div", class_=f"seplan-legend__bar_{self.id_}")
        self.labels_div = sw.Html(
            tag="div", class_=f"seplan-legend__labels_{self.id_}"
        )

        self.style = sw.Html(tag="style")

        # The wrapper class lets us target the surrounding ``.leaflet-control``
        # via a parent selector, so even if Leaflet's default float is
        # overridden somewhere, we can force the legend back to the right.
        body = sw.Html(
            tag="div",
            class_=(
                f"seplan-legend seplan-legend_{self.id_} "
                f"seplan-legend-anchor-{self.id_}"
            ),
            children=[self.style, self.title_div, self.bar_div, self.labels_div],
        )

        super().__init__(
            widget=body,
            position="bottomright",
        )

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
        gradient_css = get_color_css(type_, colors)

        # Justify labels: 2 stops → space-between, 3+ → evenly spaced.
        justify = "space-between" if len(names) <= 3 else "space-around"

        style = f"""
        .seplan-legend_{self.id_} {{
            font-family: Roboto, sans-serif;
            background: rgba(33, 33, 33, 0.85);
            color: #fff;
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 12px;
            display: inline-flex;
            flex-direction: column;
            gap: 4px;
            width: fit-content;
            min-width: 220px;
            max-width: 90vw;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
        }}

        .seplan-legend__title_{self.id_} {{
            font-size: 11px;
            opacity: 0.85;
            text-align: center;
            line-height: 1.2;
        }}

        .seplan-legend__bar_{self.id_} {{
            height: 12px;
            border-radius: 3px;
            min-width: 200px;
            {gradient_css}
        }}

        .seplan-legend__labels_{self.id_} {{
            display: flex;
            justify-content: {justify};
            font-size: 11px;
            opacity: 0.85;
            line-height: 1.2;
        }}

        .seplan-legend__labels_{self.id_} > span {{
            white-space: nowrap;
        }}
        """

        self.title_div.children = [title]
        self.bar_div.children = []
        self.labels_div.children = [
            sw.Html(tag="span", children=[name]) for name in names
        ]
        self.style.children = [style]


def get_color_css(type_, colors):
    """Generate a CSS background gradient for the legend bar.

    ``gradient`` produces a smooth linear gradient; ``stepped`` produces
    discrete color blocks of equal width.
    """
    if type_ == "gradient":
        return f"background: linear-gradient(to right, {', '.join(colors)});"

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
        if i == num_colors - 1:
            segments.append(f"{color} {start:.2f}%")
        else:
            segments.append(f"{color} {start:.2f}% {end:.2f}%")

    return f"background: linear-gradient(to right, {', '.join(segments)});"
