from typing import Literal
import ipyvuetify as v
from component.parameter.gui_params import SUITABILITY_LEVELS
from component.parameter.vis_params import SUITABILITY_COLORS
from component.types import SummaryStatsDict
from component.widget.buttons import IconBtn

DISPLAY_TYPES: list = ["absolute", "percentage", "both"]


def get_table_table_body(
    summary_stats,
    suitability_levels,
    display_type: Literal["absolute", "percentage", "both"] = "both",
):

    # Create table body
    rows = []
    for area_name, area_data in summary_stats.items():
        # Map image to sum
        image_sums = {v["image"]: v["sum"] for v in area_data["suitability"]["values"]}
        total_sum = sum(image_sums.get(level, 0) for level in suitability_levels)

        # Create table cells
        tds = [v.Html(tag="td", children=[area_name])]
        for level in suitability_levels:
            value = image_sums.get(level, 0)
            if total_sum > 0:
                percentage = (value / total_sum) * 100
            else:
                percentage = 0.0

            if display_type == "absolute":
                cell_content = f"{value:,.1f}"
            elif display_type == "percentage":
                cell_content = f"{percentage:.1f}%"
            else:
                cell_content = f"{value:,.1f} ({percentage:.1f}%)"
            tds.append(
                v.Html(
                    tag="td",
                    class_="text-right",
                    children=[cell_content],
                )
            )
        row = v.Html(tag="tr", children=tds)
        rows.append(row)

    # Assemble the table
    return [v.Html(tag="tbody", children=rows)]


def get_summary_table(
    summary_stats: SummaryStatsDict,
    display_type: Literal["absolute", "percentage", "both"] = "both",
):

    btn_switch = IconBtn("mdi-swap-horizontal", class_="ml-2")

    # Pre-sort the suitability levels
    suitability_levels = sorted(SUITABILITY_LEVELS.keys())

    # Create table headers
    headers = [v.Html(tag="th", children=["Area", btn_switch])] + [
        v.Html(
            tag="th",
            style_=f"color: {SUITABILITY_COLORS[level]}",
            class_="text-right",
            children=[SUITABILITY_LEVELS[level]],
        )
        for level in suitability_levels
    ]
    header_row = v.Html(tag="tr", children=headers)
    w_header = [v.Html(tag="thead", children=[header_row])]

    w_body = get_table_table_body(summary_stats, suitability_levels, display_type)

    table = v.SimpleTable(small=True, xs12=True, children=w_header + w_body)

    # Initialize display type index
    display_type_index = DISPLAY_TYPES.index(display_type)

    def toggle_display_type(widget, event, data):

        nonlocal display_type_index
        # Increment the index and loop back to 0 if it exceeds the length
        display_type_index = (display_type_index + 1) % len(DISPLAY_TYPES)
        new_display_type = DISPLAY_TYPES[display_type_index]

        w_body = get_table_table_body(
            summary_stats, suitability_levels, new_display_type
        )
        table.children = w_header + w_body

    btn_switch.on_event("click", toggle_display_type)

    return table
