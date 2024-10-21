from component.message import cm
from component.tile.custom_aoi_tile import AoiTile


def test_aoi_tile(empty_recipe, alert):

    recipe = empty_recipe
    aoi_tile = AoiTile(recipe=recipe)

    # Select a lmic country
    aoi_tile.view.model.admin = "959"
    # the model increases the updated trait, and this trait is listened by the view
    aoi_tile.view.model.set_object(method="ADMIN1")

    # TODO: this is a wild return from this function. It should return a boolean only

    in_lmic = aoi_tile._check_lmic(None)

    assert in_lmic == aoi_tile

    # Select a non lmic country
    aoi_tile.view.model.admin = "259"
    aoi_tile.view.model.set_object(method="ADMIN1")

    in_lmic = aoi_tile._check_lmic(None)

    assert in_lmic.view.alert.children[0].children == [cm.aoi.not_lmic]
