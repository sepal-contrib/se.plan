"""Test GAUL 2015 → 2024 admin code migration during recipe import."""

import json

import pygaul

import component.parameter as cp


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

    new_code = mapping["1521"]  # gaul1_code column is string dtype in pygaul
    match = df[df["gaul1_code"] == new_code]
    assert len(match) > 0
    assert match["gaul0_name"].iloc[0] == "Indonesia"
    assert match["gaul1_name"].iloc[0] == "Jawa Timur"
