"""Define functions to create the plots for the dashboard tile."""

from ipecharts.option import Option, Legend, Tooltip, XAxis, YAxis, Title, Grid, Toolbox
from ipecharts.option.series import Bar, Pie
from ipecharts.echarts import EChartsWidget

from typing import Dict, List, Tuple, Any

from component.parameter.gui_params import SUITABILITY_LEVELS
from component.parameter.vis_params import SUITABILITY_COLORS
from component.types import SummaryStatsDict


def get_level_name(code: int) -> str:
    return SUITABILITY_LEVELS.get(code, f"Code {code}")


def get_level_color(code: int) -> str:
    return SUITABILITY_COLORS.get(code, "#000")  # Default to black if unknown


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
    colors: List[Tuple[str]],
    series_names: List[str],
    custom_color: bool = False,
) -> List[Bar]:
    """Create a list of bar series from the series data."""

    assert len(values) == len(colors) == len(series_names)

    bars = []
    for i, series_name in enumerate(series_names):
        bars.append(
            Bar(
                data=[
                    {
                        "value": value,
                        "itemStyle": {"color": color if custom_color else None},
                    }
                    for value, color in zip(values[i], colors[i])
                ],
                name=series_name,
                type="bar",
            )
        )

    return bars


def get_bars_chart(
    categories: Tuple,
    values: Tuple,
    colors: str,
    series_names: List,
    custom_color: bool = False,
    bars_width: int = 30,
    show_legend: bool = True,
) -> EChartsWidget:
    """Create a simple, horizontal bar chart."""

    height = max(170, 50 + bars_width * len(categories))
    axis_label = {
        "inside:": True,
        "overflow": "breakAll",
        "width": 60,
        "height": 15,
        "fontSize": 12,
    }

    series = get_bars_series(
        values, colors, series_names=series_names, custom_color=custom_color
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


def get_stacked_bars_chart(summary_results: SummaryStatsDict) -> EChartsWidget:
    """Create a stacked, horizontal bar chart with a legend."""

    region_names, level_names, series_data = parse_suitability_data(summary_results)
    bars = get_stacked_series(series_data)

    selected = {name: True for name in level_names}
    selected["Unsuitable land"] = False

    height = max(200, 50 + 75 * len(region_names))
    axis_label = {
        "inside:": True,
        "overflow": "breakAll",
        "width": 60,
        "height": 15,
    }

    title = Title(text="Suitability for each region", left="center", subtext="Total")

    option = Option(
        backgroundColor="#1e1e1e00",
        # title=title,
        legend=Legend(data=level_names, selected=selected, top=0),
        yAxis=YAxis(type="category", axisLabel=axis_label, data=region_names),
        xAxis=XAxis(type="value"),
        series=bars,
        tooltip=Tooltip(),
    )
    return EChartsWidget(option=option, style={"height": f"{height}px"})


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
