from component.message import cm


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
