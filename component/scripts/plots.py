"""Define functions to create the plots for the dashboard tile."""

from component.types import RecipeStatsDict, SummaryStatsDict

import ipyvuetify as v
from ipecharts.option import Option, Legend, Tooltip, XAxis, YAxis, Grid, Toolbox
from ipecharts.option.series import Bar
from ipecharts.echarts import EChartsWidget

from typing import Dict, List, Tuple, Any

from component.parameter.gui_params import SUITABILITY_LEVELS
from component.parameter.vis_params import SUITABILITY_COLORS
from component.types import SummaryStatsDict


def get_level_name(code: int) -> str:
    return SUITABILITY_LEVELS.get(code, f"Code {code}")


def get_level_color(code: int) -> str:
    return SUITABILITY_COLORS.get(code, "#000")  # Default to black if unknown


class EChartsWidget(EChartsWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = "svg"
        self.theme = self.get_theme()
        v.theme.observe(self.set_theme, "dark")

    def get_theme(self):
        return "dark" if v.theme.dark else "light"

    def set_theme(self, _):
        self.theme = self.get_theme()


def parse_suitability_data(
    summary_results: SummaryStatsDict,
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Parse the suitability theme data from the summary results

    Returns a tuple of region names, level names, and series data for the ECharts widget.
    """

    region_names = list(summary_results.keys())
    level_codes_set = set()
    level_data_dict: Dict[str, List[float]] = {}

    # Collect all unique level codes from the data
    for region in region_names:
        suitability_values = summary_results[region]["suitability"]["values"]
        for item in suitability_values:
            code = item["image"]
            level_codes_set.add(code)

    # Sort level codes to maintain consistent order
    level_codes = sorted(level_codes_set)
    level_names = [get_level_name(code) for code in level_codes]

    # Initialize level_data_dict with empty lists
    for level_name in level_names:
        level_data_dict[level_name] = []

    # Populate level_data_dict with sum values for each region
    for region in region_names:
        suitability_values = summary_results[region]["suitability"]["values"]
        code_to_sum = {item["image"]: item["sum"] for item in suitability_values}
        # Append sum values to level_data_dict, filling missing levels with 0
        for code in level_codes:
            level_name = get_level_name(code)
            sum_value = code_to_sum.get(code, 0.0)
            level_data_dict[level_name].append(sum_value)

    # Prepare series_data in the format expected by get_bars
    series_data = []
    for level_name in level_names:
        data = level_data_dict[level_name]
        # Find the code corresponding to the level name
        code = next((k for k, v in SUITABILITY_LEVELS.items() if v == level_name), None)
        color = get_level_color(code)
        series_item = {
            "name": level_name,
            "type": "bar",
            "data": data,
            "itemStyle": {"color": color},
            "stack": "Total" if level_name != "Unsuitable land" else None,
        }
        series_data.append(series_item)

    return region_names, level_names, series_data


def parse_layer_data(
    summary_results: SummaryStatsDict, layer_id: str
) -> Tuple[List[str], List[float], List[str]]:
    """Returns a tuple of statistics for a given layer.

    Returns a tuple of region names, values, and colors for the ECharts widget.
    """

    aoi_names = []
    values = []
    colors = []

    # We know the layer_id is unique among all the themes
    for aoi_name, aoi_data in summary_results.items():
        for theme, layers in aoi_data.items():

            if theme in ["suitability", "color"]:
                continue

            for layer_dict in layers:
                if layer_dict.get(layer_id):
                    layer_data = layer_dict[layer_id]

                    aoi_names.append(aoi_name)
                    values.append(layer_data["values"][0])
                    colors.append(summary_results[aoi_name]["color"])

    return aoi_names, values, colors


def get_stacked_series(series_data: List[dict]) -> List[Bar]:
    """Create a list of echar bars from the series data."""
    bars = []

    for series in series_data:
        series["data"] = [round(value, 2) for value in series["data"]]
        bars.append(
            Bar(
                **{
                    "type": "bar",
                    "name": series["name"],
                    "stack": series["stack"],
                    "data": series["data"],
                    "itemStyle": series["itemStyle"],
                }
            )
        )
    return bars


def get_bars_series(
    values: List[Tuple[float]],
    series_names: List[str],
    series_colors: List[str] = [],
    custom_item_color: bool = False,
    custom_item_colors: List[Tuple[str]] = None,
) -> List[Bar]:
    """Create a list of bar series from the series data.

    Args:
        values: A list of tuples containing the int values for each series.
        series_colors: A list of tuples containing the str colors for each series.
        series_names: A list of names for each series.
        custom_item_color: A boolean indicating whether to use custom colors for each of the series item.
        custom_item_colors: A list of tuples containing the str colors for each of the elements of the series item.
    """

    # Do sanity checks
    if len(values) != len(series_names):
        raise ValueError(
            "The number of series names does not match the number of values series."
        )

    if custom_item_color and len(custom_item_colors) != len(values):
        raise ValueError(
            "The number of colors does not match the number of values series."
        )

    if not series_colors:
        series_colors = [None] * len(series_names)

    if not custom_item_colors:
        custom_item_colors = [[None] * len(value) for value in values]

    bars = []
    for i, series_name in enumerate(series_names):
        bars.append(
            Bar(
                data=[
                    {
                        "value": round(value, 2),
                        "itemStyle": {"color": color if custom_item_color else None},
                    }
                    for value, color in zip(values[i], custom_item_colors[i])
                ],
                itemStyle={"color": series_colors[i]},
                name=series_name,
                type="bar",
            )
        )

    return bars


def get_bars_chart(
    categories: List[str],
    values: List[List[float]],
    series_names: List[str],
    series_colors: List[str] = [],
    custom_item_colors: List[str] = [],
    custom_item_color: bool = False,
    bars_width: int = 30,
    show_legend: bool = True,
) -> EChartsWidget:
    """Create a simple, horizontal bar chart."""

    height = max(170, 50 + bars_width * len(categories))
    axis_label = {
        "inside:": True,
        "overflow": "breakAll",
        "width": 85,
        "height": 15,
        "fontSize": 12,
    }

    series = get_bars_series(
        values,
        series_names=series_names,
        series_colors=series_colors,
        custom_item_color=custom_item_color,
        custom_item_colors=custom_item_colors,
    )

    option = Option(
        backgroundColor="#1e1e1e00",
        yAxis=YAxis(type="category", axisLabel=axis_label, data=categories),
        xAxis=XAxis(type="value"),
        series=series,
        tooltip=Tooltip(trigger="axis", axisPointer={"type": "shadow"}),
        legend=Legend() if show_legend else None,
    )

    return EChartsWidget(option=option, style={"height": f"{height}px"})


def get_stacked_bars_chart(
    summary_results: SummaryStatsDict, show_legend: bool = True
) -> EChartsWidget:
    """Create a stacked, horizontal bar chart with a legend.

    This one will be used for the suitability index.

    """
    region_names, level_names, series_data = parse_suitability_data(summary_results)
    bars = get_stacked_series(series_data)

    selected = {name: True for name in level_names}
    selected["Unsuitable land"] = False

    height = str(max(200, 50 + 75 * len(region_names)))
    axis_label_y = {
        "inside:": True,
        "overflow": "breakAll",
        "width": 60,
        "height": 15,
    }
    axis_label_x = {
        "show": False,
    }

    legend = Legend(data=level_names, selected=selected, top=0, show=show_legend)

    option = Option(
        backgroundColor="#1e1e1e00",
        legend=legend,
        yAxis=YAxis(
            type="category",
            axisLabel=axis_label_y,
            data=region_names,
        ),
        xAxis=XAxis(type="value", axisLabel=axis_label_x, splitLine={"show": False}),
        series=bars,
        tooltip=Tooltip(trigger="axis", axisPointer={"type": "shadow"}),
    )
    # style={"height": f"{height}px"}
    return EChartsWidget(option=option, height=height, rederer="svg")


def get_individual_charts(summary_results: SummaryStatsDict):
    """Create individual charts for each region with stacked, horizontal bars and no legend."""

    charts = []
    for region, data in summary_results.items():
        suitability_values = data["suitability"]["values"]
        code_to_sum = {item["image"]: item["sum"] for item in suitability_values}
        level_codes = sorted(code_to_sum.keys())
        level_names = [get_level_name(code) for code in level_codes]
        values = [code_to_sum[code] for code in level_codes]
        colors = [get_level_color(code) for code in level_codes]

        # Since we're stacking, we need to create one series per level
        bars = []
        for i in range(len(level_codes)):
            bar = Bar(
                **{
                    "type": "bar",
                    "name": level_names[i],
                    "data": [values[i]],
                    "itemStyle": {"color": colors[i]},
                    "stack": "Total",  # Stack all bars together
                }
            )
            bars.append(bar)

        # Configure the chart to be horizontal by swapping xAxis and yAxis
        selected = {name: True for name in level_names}
        selected["Unsuitable land"] = False

        option = Option(
            legend=Legend(data=level_names, selected=selected),
            backgroundColor="#1e1e1e00",
            # title=Title(text=f"Suitability for {region}"),
            xAxis=XAxis(type="value"),
            # yAxis=YAxis(type="category", rotate=90, data=[region]),
            yAxis=YAxis(type="category", data=[region]),
            series=bars,
            tooltip=Tooltip(trigger="axis", axisPointer={"type": "shadow"}),
            grid=Grid(height="60px"),
            toolbox=Toolbox(show=True),
        )
        charts.append(EChartsWidget(option=option, style={"height": "150px"}))

    return charts


def get_suitability_charts(
    recipes_stats: List[RecipeStatsDict], test=False
) -> List[EChartsWidget]:
    """Create a list of charts for each of the recipe stats."""
    # We can do two things, either we display the summary for all the scenarios
    # In the same chart or we display them separately... I think it's better to
    # display them separately
    charts = []
    for i, recipe_stats in enumerate(recipes_stats):
        recipe_name, summary_stats = list(recipe_stats.items())[0]

        # Get the summary statistics for the suitability theme
        charts.append(get_stacked_bars_chart(summary_stats, show_legend=i == 0))

    return charts if not test else v.Card(children=[v.CardText(children=charts)])
