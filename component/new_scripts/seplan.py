"""All tools to build the suitability index"""
from typing import List

from sepal_ui.aoi import AoiModel
import ee

from component import new_model as cmod


def _percentile(
    ee_image: ee.Image,
    aoi: ee.FeatureCollection,
    scale: int = 10000,
    percentile: List[int] = [3, 97],
) -> ee.Image:
    """Return a normalized version of the layer image"""
    ee_image = ee_image.select(0)
    percents = ee_image.rename("img").reduceRegion(
        reducer=ee.Reducer.percentile(percentiles=percentile),
        geometry=aoi.geometry(),
        scale=scale,
    )
    low = ee.Number(percents.get(f"img_p{percentile[0]}"))
    high = ee.Number(percents.get(f"img_p{percentile[1]}")).add(0.1e-13)

    return ee_image.unitScale(low, high).clamp(0, 1).float()


def _min_max(
    ee_image: ee.Image,
    aoi: ee.FeatureCollection,
    scale: int = 10000,
) -> ee.Image:
    """Return a normalized version of the layer image"""
    ee_image = ee_image.select(0)
    min_max = ee_image.rename("img").reduceRegion(
        reducer=ee.Reducer.minMax(), geometry=aoi.geometry(), scale=scale
    )
    low = ee.Number(min_max.get("img_min"))
    high = ee.Number(min_max.get("img_max")).add(0.1e-13)

    return ee_image.unitScale(low, high).float()


class Seplan:

    # -- model parameters -----------------------
    aoi_model: AoiModel
    cost_model: cmod.CostModel
    priority_model: cmod.PriorityModel
    constraint_model: cmod.ConstraintModel

    def __init__(
        self,
        aoi_model: AoiModel,
        priority_model: cmod.PriorityModel,
        cost_model: cmod.CostModel,
        constraint_model=cmod.ConstraintModel,
    ):
        """A class to compute the different indices of seplan.

        We use a class instead of a comparaison to be able to compare multiple scenarios
        """

        # save the models as members
        self.aoi_model = aoi_model
        self.cost_model = cost_model
        self.priority_model = priority_model
        self.constraint_model = constraint_model

    def get_priority_index(self, clip: bool = False) -> ee.Image:
        """Build the index exclusively on the benefits weighted approach"""

        # normaized all the priority on the aoi
        aoi = self.aoi_model.feature_collection
        images = [_percentile(ee.Image(i), aoi) for i in self.priority_model.assets]

        default = {"image": ee.Image(0), "weight": 0, "nb": 0}
        theme_images = {k: default.copy() for k in set(self.priority_model.themes)}
        for idx, image in enumerate(images):
            theme_image = theme_images[self.priority_model.themes[idx]]
            theme_image["image"] = theme_image["image"].add(image)
            theme_image["weight"] += self.priority_model.weights[idx]
            theme_image["nb"] += 1

        for v in theme_images.values():
            v["weight"] = round(v["weight"] / v["nb"], 5)

        index = ee.Image(0)
        for v in theme_images.values():
            index = index.add(v["image"].divide(ee.Image(v["weight"])))
        index = _min_max(index, aoi)

        return index.clip(aoi) if clip is True else index

    def get_priority_cost_index(self) -> ee.Image:

        pass

    def get_constraint_index(self) -> ee.Image:

        pass
