import pandas as pd
from component import parameter as cp

layers = pd.read_csv(cp.layer_list).fillna("")
default_asset_id = layers[layers.layer_id == "treecover_with_potential"][
    "gee_asset"
].values[0]
