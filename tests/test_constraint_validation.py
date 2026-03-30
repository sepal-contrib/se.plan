"""Tests for constraint validation and safe import functionality."""

import pytest
from component.scripts.validation import (
    validate_constraint_values,
    validate_constraint_data,
    filter_invalid_constraints,
)


# -- validate_constraint_values --


def test_valid_binary_zero():
    is_valid, error = validate_constraint_values([0], "binary", "test_layer")
    assert is_valid is True
    assert error == ""


def test_valid_binary_one():
    is_valid, error = validate_constraint_values([1], "binary", "test_layer")
    assert is_valid is True
    assert error == ""


def test_invalid_binary_wrong_value():
    is_valid, error = validate_constraint_values([50], "binary", "test_layer")
    assert is_valid is False
    assert "0 or 1" in error


def test_invalid_binary_multiple_values():
    is_valid, error = validate_constraint_values([0, 1], "binary", "test_layer")
    assert is_valid is False
    assert "exactly one value" in error


def test_valid_categorical():
    is_valid, error = validate_constraint_values(
        [1, 2, 3], "categorical", "test_layer"
    )
    assert is_valid is True
    assert error == ""


def test_invalid_categorical_empty():
    is_valid, error = validate_constraint_values([], "categorical", "test_layer")
    assert is_valid is False
    assert "at least one" in error


def test_valid_continuous():
    is_valid, error = validate_constraint_values([10, 100], "continuous", "test_layer")
    assert is_valid is True
    assert error == ""


def test_invalid_continuous_single_value():
    is_valid, error = validate_constraint_values([10], "continuous", "test_layer")
    assert is_valid is False
    assert "min and max" in error


def test_invalid_continuous_min_greater_than_max():
    is_valid, error = validate_constraint_values([100, 10], "continuous", "test_layer")
    assert is_valid is False
    assert "less than max" in error


# -- validate_constraint_data --


def _make_constraints_data(**overrides):
    """Build a minimal valid constraints data dict with optional overrides."""
    data = {
        "names": ["Layer 1", "Layer 2"],
        "ids": ["layer_1", "layer_2"],
        "values": [[0], [1, 2, 3]],
        "data_type": ["binary", "categorical"],
        "themes": ["custom", "custom"],
        "assets": ["asset1", "asset2"],
        "descs": ["desc1", "desc2"],
        "units": ["0/1", "classes"],
    }
    data.update(overrides)
    return data


def test_valid_constraints_data():
    is_valid, invalid = validate_constraint_data(_make_constraints_data())
    assert is_valid is True
    assert len(invalid) == 0


def test_invalid_binary_values_in_data():
    data = _make_constraints_data(
        names=["Bad Binary"],
        ids=["bad_binary"],
        values=[[50, 40, 80]],
        data_type=["binary"],
        themes=["custom"],
        assets=["asset1"],
        descs=["desc1"],
        units=["0/1"],
    )

    is_valid, invalid = validate_constraint_data(data)
    assert is_valid is False
    assert len(invalid) == 1
    assert invalid[0]["name"] == "Bad Binary"
    assert "0 or 1" in invalid[0]["error"]


def test_mismatched_array_lengths():
    data = _make_constraints_data(ids=["layer_1"])  # 1 id but 2 names

    is_valid, invalid = validate_constraint_data(data)
    assert is_valid is False
    assert any("length" in str(item.get("error", "")).lower() for item in invalid)


def test_multiple_invalid_constraints():
    data = _make_constraints_data(
        names=["Bad Binary", "Empty Categorical", "Good Binary"],
        ids=["bad_1", "bad_2", "good_1"],
        values=[[50], [], [1]],
        data_type=["binary", "categorical", "binary"],
        themes=["custom", "custom", "custom"],
        assets=["asset1", "asset2", "asset3"],
        descs=["desc1", "desc2", "desc3"],
        units=["0/1", "classes", "0/1"],
    )

    is_valid, invalid = validate_constraint_data(data)
    assert is_valid is False
    assert len(invalid) == 2
    assert invalid[0]["name"] == "Bad Binary"
    assert invalid[1]["name"] == "Empty Categorical"


# -- filter_invalid_constraints --


def test_filter_removes_invalid_keeps_valid():
    data = _make_constraints_data(
        names=["Good Binary", "Bad Binary", "Good Categorical"],
        ids=["good_1", "bad_1", "good_2"],
        values=[[0], [50], [1, 2, 3]],
        data_type=["binary", "binary", "categorical"],
        themes=["custom", "custom", "custom"],
        assets=["asset1", "asset2", "asset3"],
        descs=["desc1", "desc2", "desc3"],
        units=["0/1", "0/1", "classes"],
    )

    filtered, removed = filter_invalid_constraints(data)

    assert len(filtered["ids"]) == 2
    assert filtered["names"] == ["Good Binary", "Good Categorical"]
    assert filtered["ids"] == ["good_1", "good_2"]
    assert len(removed) == 1
    assert removed[0]["name"] == "Bad Binary"


def test_filter_all_valid_returns_unchanged():
    data = _make_constraints_data()

    filtered, removed = filter_invalid_constraints(data)

    assert filtered == data
    assert len(removed) == 0


def test_filter_preserves_extra_keys():
    data = _make_constraints_data(
        names=["Good Binary"],
        ids=["good_1"],
        values=[[0]],
        data_type=["binary"],
        themes=["custom"],
        assets=["asset1"],
        descs=["desc1"],
        units=["0/1"],
        updated=5,
        new_changes=2,
    )

    filtered, removed = filter_invalid_constraints(data)

    assert filtered["updated"] == 5
    assert filtered["new_changes"] == 2
