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
