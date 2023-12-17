import pandas as pd


def export_as_csv(recipe_session_path, summary_stats):
    # Function to create a multi-row format for each sub-category
    print(recipe_session_path)
    formatted_data = []
    for area_data in summary_stats:
        for area, contents in area_data.items():
            for category, details in contents.items():
                if isinstance(details, list):  # For 'benefit', 'constraint', 'cost'
                    for item in details:
                        for sub_category, value in item.items():
                            row = {
                                "Area": area,
                                "Category": category,
                                "Sub-category": sub_category,
                                "Total": value["total"][0],
                                "Values": value["values"][0],
                            }
                            formatted_data.append(row)
                elif isinstance(details, dict):  # For 'suitability'
                    for value in details["values"]:
                        row = {
                            "Area": area,
                            "Category": category,
                            "Sub-category": f'image_{value["image"]}',
                            "Total": None,
                            "Values": value["sum"],
                        }
                        formatted_data.append(row)
                    # Adding total suitability as a separate row
                    formatted_data.append(
                        {
                            "Area": area,
                            "Category": category,
                            "Sub-category": "total",
                            "Total": details["total"],
                            "Values": None,
                        }
                    )

    formatted_df = pd.DataFrame(formatted_data)

    # Exporting the reformatted DataFrame to an Excel file
    formatted_df.to_excel(recipe_session_path, index=False)
