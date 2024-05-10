from component.scripts.ui_helpers import get_categorical_values, parse_export_name
from component.message import cm


def test_parse_export_name():
    """Test parse_export_name function."""

    input_str = "index_constraint_index_recipe_2024-05-08-081336_gee"
    expected_output = "index_suitability_recipe_2024-05-08-081336_gee"

    assert parse_export_name(input_str) == expected_output

    input_str = "index_recipe_2024-05-08-081336_gee"

    assert parse_export_name(input_str) == input_str

    input_str = "index_benefit_cost_index_test_cundinamarca"
    expected_output = "index_benefit_cost_test_cundinamarca"

    assert parse_export_name(input_str) == expected_output

    input_str = "index_benefit_index_test_cundinamarca"
    expected_output = "index_benefit_test_cundinamarca"

    assert parse_export_name(input_str) == expected_output


def test_get_categorical_values():

    asset = "no_asset/asdf"
    values = [1, 2, 3]

    assert get_categorical_values(asset, values) == values

    asset = "COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019"
    values = [1, 2, 3]
