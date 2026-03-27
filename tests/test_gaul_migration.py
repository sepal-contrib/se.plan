"""Test GAUL 2015 → 2024 admin code migration during recipe import."""

import json
from pathlib import Path

import pygaul

import component.parameter as cp


def _migrate_gaul_code(admin_code, name=None):
    """Local copy of the migration function for testing without full import chain."""
    if not admin_code:
        return admin_code
    code = str(admin_code)
    df = pygaul._df()
    if name:
        iso3_from_name = name.split("_")[0]
        match = df[
            (df["gaul0_code"].astype(str) == code)
            | (df["gaul1_code"].astype(str) == code)
            | (df["gaul2_code"].astype(str) == code)
        ]
        if len(match) > 0 and match["iso3_code"].iloc[0] == iso3_from_name:
            return code
    mapping = json.loads(cp.gaul_migration_map.read_text())
    return mapping.get(code, code)


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
    assert _migrate_gaul_code("1521", "IDN_Jawa_Timur") == "2625"
    assert _migrate_gaul_code("959", "COL_Risaralda") == "1938"


def test_new_code_not_translated_with_name():
    """GAUL 2024 code + matching recipe name -> kept as-is (no collision)."""
    assert _migrate_gaul_code("2625", "IDN_Jawa_Timur") == "2625"


def test_null_admin_passthrough():
    """Null admin code passes through unchanged."""
    assert _migrate_gaul_code(None) is None


def test_no_name_falls_through_to_mapping():
    """Without a name, always applies the mapping."""
    assert _migrate_gaul_code("1521") == "2625"
