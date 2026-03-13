import json
from typing import Dict, List, Union

from component.message import cm
from sepal_ui.scripts import utils as su
from component.parameter.file_params import legends_path
import logging

logger = logging.getLogger("SEPLAN")


def set_default_asset(w_asset_items: list, asset: str) -> list:
    """Add the default asset as the first item of the list if it is not already present.

    And replace the existing default asset if it is not the same as the new one.

    Args:
        w_asset_items (list): list of current items of the asset combo box
        asset (str): default asset
    """
    header = {"header": cm.default_asset_header}
    default_asset_item = [header, asset]

    if header not in w_asset_items:
        return default_asset_item + w_asset_items

    if w_asset_items[1] != asset:
        return default_asset_item + w_asset_items[2:]


def get_categorical_values(
    asset: str, values: List[int]
) -> Union[List[int], List[Dict]]:
    """Returns a list of items based on known legends for the categorical widget.

    Args:
        asset (str): asset name
        values (list): list of pixel values
    """

    # Load legends JSON file
    try:
        with open(legends_path, "r") as file:
            json_data = json.load(file)
    except FileNotFoundError:
        logger.debug("Error: The file was not found.")
        return values
    except json.JSONDecodeError:
        logger.debug("Error: File is not a valid JSON.")
        return values

    # Check if the asset exists in the json data and has a legend
    if asset in json_data and "legend" in json_data[asset]:
        legend = json_data[asset]["legend"]
        # Create a list of dictionaries based on the legend and input values

        result = [
            {
                "text": f"{str(value)} : {legend.get(str(value), 'Unknown')}",
                "value": value,
            }
            for value in values
        ]

        return result
    else:
        # Return the original values if no legend is found for the asset
        return values


def parse_export_name(name: str) -> str:
    """for constraint_index, benefit_index and benefit_cost_index return
    the translated key."""

    index_names = ["constraint_index", "benefit_index", "benefit_cost_index"]

    for index_name in index_names:
        if index_name in name:
            if index_name in cm.layer.index:
                key_value = cm.layer.index[index_name]["name"].replace("index", "")
                readable_name = su.normalize_str(key_value).lower()
                return name.replace(index_name, readable_name).replace("__", "_")

    return name
