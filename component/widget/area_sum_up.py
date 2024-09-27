from typing import Literal
import ipyvuetify as v
from component.parameter.gui_params import SUITABILITY_LEVELS
from component.parameter.vis_params import SUITABILITY_COLORS


def get_summary_table(
    summary_stats, display_type: Literal["absolute", "percentage", "both"] = "both"
):

    # Pre-sort the suitability levels
    suitability_levels = sorted(SUITABILITY_LEVELS.keys())

    # Create table headers
    headers = [v.Html(tag="th", children=["Area"])] + [
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
    w_body = [v.Html(tag="tbody", children=rows)]
    table = v.SimpleTable(small=True, xs12=True, children=w_header + w_body)

    return table
