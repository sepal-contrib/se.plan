from typing import List

import pandas as pd

import component.parameter.gui_params as param
from component.parameter.directory import result_dir


def export_as_csv(recipe_session_name: str, summary_stats: List[dict]):
    # Function to create a multi-row format for each sub-category
    csv_folder = result_dir / "results"
    csv_folder.mkdir(exist_ok=True)
    session_results_path = (csv_folder / recipe_session_name).with_suffix(".csv")

    formatted_data = []
    for area_data in summary_stats:
        for area, contents in area_data.items():
            for category, details in contents.items():
                if isinstance(details, list):  # For 'benefit', 'constraint', 'cost'
                    for item in details:
                        for sub_category, value in item.items():
                            row = {
                                "Area": area,
                                "Theme": category,
                                "Sub-theme": sub_category,
                                "Values": value["values"][0],
                            }
                            formatted_data.append(row)
                elif isinstance(details, dict):  # For 'suitability'
                    for value in details["values"]:
                        row = {
                            "Area": area,
                            "Theme": category,
                            "Sub-theme": param.SUITABILITY_LEVELS[value["image"]],
                            "Values": value["sum"],
                        }
                        formatted_data.append(row)
                    # Adding total suitability as a separate row
                    formatted_data.append(
                        {
                            "Area": area,
                            "Theme": "Total",
                            "Sub-theme": "Total",
                            "Values": details["total"],
                        }
                    )

    formatted_df = pd.DataFrame(formatted_data)
    formatted_df.to_csv(session_results_path, index=False)

    return session_results_path
