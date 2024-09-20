"""Define functions to create the plots for the dashboard tile."""

from ipecharts.option import Option, Legend, Tooltip, XAxis, YAxis, Title, Grid, Toolbox
from ipecharts.option.series import Bar
from ipecharts.echarts import EChartsWidget

from typing import Dict, List, Tuple, Any

from component.parameter.gui_params import SUITABILITY_LEVELS
from component.parameter.vis_params import SUITABILITY_COLORS


def get_level_name(code: int) -> str:
    return SUITABILITY_LEVELS.get(code, f"Code {code}")


def get_level_color(code: int) -> str:
    return SUITABILITY_COLORS.get(code, "#000")  # Default to black if unknown


def parse_suitability(
    summary_results: Dict[str, Any]
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
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


def get_bars(series_data):
    """Create a list of bar series from the series data."""
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


def get_chart(summary_results):
    region_names, level_names, series_data = parse_suitability(summary_results)
    bars = get_bars(series_data)

    selected = {name: True for name in level_names}
    selected["Unsuitable land"] = False

    option = Option(
        backgroundColor="#1e1e1e00",
        legend=Legend(data=level_names, selected=selected),
        yAxis=YAxis(type="category", data=region_names),
        xAxis=XAxis(type="value"),
        series=bars,
        tooltip=Tooltip(),
    )
    return EChartsWidget(option=option)


def get_individual_charts(summary_results):
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
            title=Title(text=f"Suitability for {region}"),
            xAxis=XAxis(type="value"),  # xAxis is value
            yAxis=YAxis(type="category", data=[region]),
            series=bars,
            tooltip=Tooltip(trigger="axis", axisPointer={"type": "shadow"}),
            grid=Grid(height="100px"),
            toolbox=Toolbox(show=True),
        )
        charts.append(EChartsWidget(option=option))

    return charts
