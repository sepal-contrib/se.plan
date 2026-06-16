from component.message import cm
from component.tile.custom_aoi_tile import AoiView


def test_aoi_tile(empty_recipe):

    recipe = empty_recipe
    aoi_tile = AoiView(map_=None, recipe=recipe)

    # Select an LMIC country (Kenya, GAUL 2024 admin code 137). _check_lmic
    # reads view.model.admin directly, so no set_object round-trip is needed.
    aoi_tile.view.model.admin = "137"
    in_lmic = aoi_tile._check_lmic(None)
    assert in_lmic is aoi_tile
    assert recipe.seplan_aoi.aoi_lmic_valid is True

    # Select a non-LMIC country (USA, GAUL 2024 admin code 220): the view flags
    # it invalid and warns the user it is out of the provided layers' scope.
    aoi_tile.view.model.admin = "220"
    in_lmic = aoi_tile._check_lmic(None)
    assert in_lmic is aoi_tile
    assert recipe.seplan_aoi.aoi_lmic_valid is False
    assert in_lmic.view.alert.children[0].children == [cm.aoi.not_lmic]


def test_lmic_verdict_tiers(empty_recipe):
    """The raster-path verdict grades land coverage into ok / warn / block."""
    recipe = empty_recipe
    aoi_tile = AoiView(map_=None, recipe=recipe)
    seplan_aoi = recipe.seplan_aoi

    # Majority LMIC (>= 0.5) → clean pass: usable, no warning. Dirty the state
    # first to prove the verdict actively clears it.
    seplan_aoi.aoi_lmic_valid = False
    seplan_aoi.aoi_lmic_warning = True
    aoi_tile._apply_lmic_verdict(0.99)
    assert seplan_aoi.aoi_lmic_valid is True
    assert seplan_aoi.aoi_lmic_warning is False

    # Partial coverage (0 < frac < 0.5) — e.g. a coastal/archipelago box — is
    # usable but warned (dialog stays open); message reports the rounded %.
    aoi_tile._apply_lmic_verdict(0.2566)
    assert seplan_aoi.aoi_lmic_valid is True
    assert seplan_aoi.aoi_lmic_warning is True
    assert aoi_tile.view.alert.children[0].children == [cm.aoi.partial_lmic.format(26)]

    # No LMIC coverage at all → hard block with the out-of-scope message.
    aoi_tile._apply_lmic_verdict(0.0)
    assert seplan_aoi.aoi_lmic_valid is False
    assert seplan_aoi.aoi_lmic_warning is False
    assert aoi_tile.view.alert.children[0].children == [cm.aoi.not_lmic]
