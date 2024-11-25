from typing import List

import pandas as pd

import component.parameter.gui_params as param
from component.parameter.directory import result_dir
from component.types import RecipeStatsDict

TYPE_OF_RESULT = {
    "benefit": "mean",
    "constraint": "percent",
    "cost": "sum",
    "suitability": "sum",
}


def export_as_csv(recipe_summary_stats: RecipeStatsDict):
    # Function to create a multi-row format for each sub-category

    recipe_name, summary_stats = list(recipe_summary_stats.items())[0]

    csv_folder = result_dir / "results"
    csv_folder.mkdir(exist_ok=True)
    session_results_path = (csv_folder / recipe_name).with_suffix(".csv")

    formatted_data = []
    for recipe_name, area_stats in recipe_summary_stats.items():
        for area_name, area_data in area_stats.items():
            for category, details in area_data.items():
                if category == "color":
                    continue
                type_result = TYPE_OF_RESULT[category]
                if isinstance(details, list):  # For 'benefit', 'constraint', 'cost'
                    for item in details:
                        for sub_category, value in item.items():
                            row = {
                                "Recipe": recipe_name,
                                "Area": area_name,
                                "Theme": category,
                                "Sub-theme": sub_category,
                                "Values": value["values"][type_result],
                            }
                            formatted_data.append(row)
                elif isinstance(details, dict):  # For 'suitability'
                    for value in details["values"]:
                        row = {
                            "Recipe": recipe_name,
                            "Area": area_name,
                            "Theme": category,
                            "Sub-theme": param.SUITABILITY_LEVELS[value["image"]],
                            "Values": value["sum"],
                        }
                        formatted_data.append(row)
                    # Adding total suitability as a separate row
                    formatted_data.append(
                        {
                            "Recipe": recipe_name,
                            "Area": area_name,
                            "Theme": "Total",
                            "Sub-theme": "Total",
                            "Values": details["total"],
                        }
                    )

    formatted_df = pd.DataFrame(formatted_data)
    formatted_df.to_csv(session_results_path, index=False)

    return session_results_path
