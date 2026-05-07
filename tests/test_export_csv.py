"""Tests for the dashboard CSV export (`component.scripts.compute.export_as_csv`)."""

import copy
import re
from pathlib import Path

import pandas as pd
import pytest

EXPECTED_COLUMNS = [
    "Recipe",
    "Area",
    "AOI type",
    "Theme",
    "Indicator",
    "Unit",
    "Aggregation",
    "Value",
]


@pytest.fixture
def single_aoi_stats():
    """A RecipeStatsDict with one primary AOI and the standard indicators."""
    return {
        "peru": {
            "PER_Amazonas": {
                "benefit": [
                    {"biodiversity_intactness": {"values": {"mean": 0.9077500730019198}, "total": [0.9]}},
                    {"endangered_species": {"values": {"mean": 18.357729356162096}, "total": [18]}},
                    {"ground_carbon": {"values": {"mean": 52.476425839602435}, "total": [52]}},
                    {"woodfuel_harvest": {"values": {"mean": 0.05340367248356664}, "total": [0.05]}},
                    {"forest_job": {"values": {"mean": 0.0011163512767639661}, "total": [0.001]}},
                    {"plantation_growth_rates": {"values": {"mean": 27.651329515315897}, "total": [27]}},
                ],
                "constraint": [
                    {"treecover_with_potential": {"values": {"percent": 65.35092275053587}, "total": [3925288]}},
                ],
                "cost": [
                    {"opportunity_cost": {"values": {"sum": 938.1267199859027}, "total": [938]}},
                    {"implementation_cost": {"values": {"sum": 521.7227209970567}, "total": [521]}},
                ],
                "suitability": {
                    "values": [
                        {"image": 1, "sum": 308810.2869463376},
                        {"image": 2, "sum": 414872.70190984395},
                        {"image": 3, "sum": 283440.90949578444},
                        {"image": 4, "sum": 240349.0361641916},
                        {"image": 5, "sum": 75298.45474935495},
                        {"image": 6, "sum": 2602516.9563359786},
                    ],
                    "total": 3925288.3456014907,
                },
                "color": "#1f77b4",
            }
        }
    }


@pytest.fixture
def multi_aoi_stats(single_aoi_stats):
    """RecipeStatsDict with primary + 2 sub-regions, perturbed values."""
    primary = single_aoi_stats["peru"]["PER_Amazonas"]

    def perturb(area_data, factor):
        new_data = copy.deepcopy(area_data)
        for entry in new_data["benefit"]:
            for content in entry.values():
                content["values"]["mean"] *= factor
        for entry in new_data["constraint"]:
            for content in entry.values():
                content["values"]["percent"] *= factor
        for entry in new_data["cost"]:
            for content in entry.values():
                content["values"]["sum"] *= factor
        for v in new_data["suitability"]["values"]:
            v["sum"] *= factor
        new_data["suitability"]["total"] *= factor
        return new_data

    return {
        "peru": {
            "PER_Amazonas": primary,
            "site_north": perturb(primary, 0.95),
            "site_south": perturb(primary, 0.85),
        }
    }


@pytest.fixture
def patch_result_dir(monkeypatch, tmp_path):
    """Redirect compute output to tmp_path."""
    from component.scripts import compute

    monkeypatch.setattr(compute, "result_dir", tmp_path)
    return tmp_path


def read_csv_with_metadata(path: Path):
    """Return (metadata_lines: list[str], dataframe)."""
    text = path.read_text(encoding="utf-8")
    metadata = [line for line in text.splitlines() if line.startswith("#")]
    df = pd.read_csv(path, comment="#")
    return metadata, df


def test_round_trip_parses_with_pandas(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    assert list(df.columns) == EXPECTED_COLUMNS


def test_metadata_header_single_aoi(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    metadata, _ = read_csv_with_metadata(Path(path))

    md = "\n".join(metadata)
    assert "# Recipe: peru" in md
    assert re.search(r"# Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", md)
    assert "# Primary AOI: PER_Amazonas" in md
    assert "# Scale (m): 100" in md
    assert "# Areas: 1" in md
    assert not any(line.startswith("# Sub-regions:") for line in metadata)


def test_metadata_header_multi_aoi(multi_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(multi_aoi_stats)
    metadata, _ = read_csv_with_metadata(Path(path))

    md = "\n".join(metadata)
    assert "# Primary AOI: PER_Amazonas" in md
    assert "# Sub-regions: site_north, site_south" in md
    assert "# Areas: 3" in md


def test_indicator_labels_are_human_readable(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    indicators = set(df["Indicator"])
    assert "Unrealized biomass potential" in indicators
    assert "Biodiversity Intactness Index" in indicators
    assert "Land opportunity cost" in indicators
    assert "Implementation cost" in indicators
    assert "Current tree cover less than potential" in indicators
    assert "Very low" in indicators
    assert "Total" in indicators


def test_units_populated(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    non_suit = df[df["Theme"] != "Suitability"]
    assert (non_suit["Unit"].astype(str).str.len() > 0).all(), \
        f"Empty units in: {non_suit[non_suit['Unit'].astype(str).str.len() == 0]}"

    suit = df[df["Theme"] == "Suitability"]
    assert (suit["Unit"] == "ha").all()


def test_constraint_unit_is_percent_of_aoi(single_aoi_stats, patch_result_dir):
    """Constraints report % of AOI covered, regardless of the layer's native unit."""
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    constraints = df[df["Theme"] == "Constraint"]
    assert len(constraints) > 0
    assert (constraints["Unit"] == "% of AOI").all()


def test_aggregation_labels(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    assert (df.loc[df["Theme"] == "Benefit", "Aggregation"] == "mean").all()
    assert (df.loc[df["Theme"] == "Constraint", "Aggregation"] == "coverage").all()
    assert (df.loc[df["Theme"] == "Cost", "Aggregation"] == "sum").all()
    assert (df.loc[df["Theme"] == "Suitability", "Aggregation"] == "area").all()


def test_numeric_precision_bounded(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    text = Path(path).read_text(encoding="utf-8")

    assert "0.9077500730019198" not in text
    assert "0.0011163512767639661" not in text
    assert "308810.2869463376" not in text


def test_sub_region_block_ordering(multi_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(multi_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    seen = []
    for area in df["Area"]:
        if area not in seen:
            seen.append(area)

    assert seen[0] == "PER — Amazonas"
    assert seen[1] == "site_north"
    assert seen[2] == "site_south"


def test_aoi_type_column(multi_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(multi_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    primary = df[df["Area"] == "PER — Amazonas"]
    assert (primary["AOI type"] == "Primary").all()

    north = df[df["Area"] == "site_north"]
    assert (north["AOI type"] == "Sub-region").all()

    south = df[df["Area"] == "site_south"]
    assert (south["AOI type"] == "Sub-region").all()


def test_per_subregion_suitability_total(multi_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(multi_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    totals = df[(df["Theme"] == "Suitability") & (df["Indicator"] == "Total")]
    assert len(totals) == 3
    assert set(totals["Area"]) == {"PER — Amazonas", "site_north", "site_south"}
    assert (totals["Aggregation"] == "area").all()


def test_special_characters_preserved(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    units = set(df["Unit"])
    assert "MgC/ha" in units
    assert any("km" in u for u in units)


def test_no_nan_strings(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    text = Path(path).read_text(encoding="utf-8")

    assert ",nan," not in text.lower()
    assert ",null," not in text.lower()
    assert ",none," not in text.lower()
    assert ",nan\n" not in text.lower()
    assert ",null\n" not in text.lower()
    assert ",none\n" not in text.lower()


def test_custom_polygon_area_name_unchanged(multi_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(multi_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    assert "site_north" in df["Area"].values
    assert "site_south" in df["Area"].values


def test_within_aoi_indicator_ordering(single_aoi_stats, patch_result_dir):
    """Within an AOI block: Benefit -> Constraint -> Cost -> Suitability classes -> Total."""
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    _, df = read_csv_with_metadata(Path(path))

    themes_in_order = list(df["Theme"])
    benefit_end = max(i for i, t in enumerate(themes_in_order) if t == "Benefit")
    constraint_start = min(i for i, t in enumerate(themes_in_order) if t == "Constraint")
    constraint_end = max(i for i, t in enumerate(themes_in_order) if t == "Constraint")
    cost_start = min(i for i, t in enumerate(themes_in_order) if t == "Cost")
    cost_end = max(i for i, t in enumerate(themes_in_order) if t == "Cost")
    suit_start = min(i for i, t in enumerate(themes_in_order) if t == "Suitability")
    last_idx = len(themes_in_order) - 1

    assert benefit_end < constraint_start
    assert constraint_end < cost_start
    assert cost_end < suit_start
    assert df.iloc[last_idx]["Indicator"] == "Total"


def test_returned_path_has_csv_extension(single_aoi_stats, patch_result_dir):
    from component.scripts.compute import export_as_csv

    path = export_as_csv(single_aoi_stats)
    assert Path(path).suffix == ".csv"
    assert Path(path).exists()
