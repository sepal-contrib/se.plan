"""Test GAUL 2015 → 2024 admin code migration during recipe import."""

import json
from pathlib import Path

import pygaul

import component.parameter as cp
from component.model.aoi_model import SeplanAoi, _migrate_gaul_code


def test_old_gaul_code_is_translated():
    """A recipe with GAUL 2015 code 1521 (Jawa Timur) should be translated to 2625."""
    mapping = json.loads(cp.gaul_migration_map.read_text())
    assert mapping["1521"] == "2625"
    assert mapping["959"] == "1938"
    assert mapping["116"] == "241"


def test_translated_code_resolves_in_pygaul():
    """The translated code should exist in the current pygaul (GAUL 2024)."""
    mapping = json.loads(cp.gaul_migration_map.read_text())
    df = pygaul._df()

    new_code = mapping["1521"]
    match = df[df["gaul1_code"].astype(str) == new_code]
    assert len(match) > 0
    assert match["gaul0_name"].iloc[0] == "Indonesia"
    assert match["gaul1_name"].iloc[0] == "Jawa Timur"


def test_old_code_translated_with_name():
    """Old GAUL 2015 code + recipe name -> translated to GAUL 2024."""
    assert _migrate_gaul_code("1521", "ADMIN1", "IDN_Jawa_Timur") == "2625"
    assert _migrate_gaul_code("959", "ADMIN1", "COL_Risaralda") == "1938"


def test_new_code_not_translated_with_name():
    """GAUL 2024 code + matching recipe name -> kept as-is (no collision)."""
    assert _migrate_gaul_code("2625", "ADMIN1", "IDN_Jawa_Timur") == "2625"


def test_null_admin_passthrough():
    """Null admin code passes through unchanged."""
    assert _migrate_gaul_code(None) is None


def test_old_code_without_name_still_translates_when_unambiguous():
    """Legacy codes that do not exist in current GAUL still translate without a name."""
    assert _migrate_gaul_code("959", "ADMIN1") == "1938"


def test_current_code_without_name_is_not_retranslated():
    """Current GAUL codes stay unchanged when the recipe name is missing."""
    assert _migrate_gaul_code("2625", "ADMIN1") == "2625"


def test_load_gaul2015_recipe_translates_admin_code():
    """Loading the gaul2015_admin1_indonesia.json recipe translates 1521 → 2625."""
    recipe_path = Path(__file__).parent / "data/recipes/gaul2015_admin1_indonesia.json"
    data = json.loads(recipe_path.read_text())

    seplan_aoi = SeplanAoi()
    seplan_aoi.import_data(data["aoi"], auto_update=False)

    assert seplan_aoi.aoi_model.admin == "2625"
    assert seplan_aoi.aoi_model.method == "ADMIN1"
