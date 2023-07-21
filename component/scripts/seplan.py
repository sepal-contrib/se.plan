"""All tools to build the suitability index."""
from typing import List

import ee

from component import model as cmod
from component.model.aoi_model import SeplanAoi


class Seplan:
    # -- model parameters -----------------------
    aoi_model: SeplanAoi
    benefit_model: cmod.BenefitModel
    constraint_model: cmod.ConstraintModel
    cost_model: cmod.CostModel

    def __init__(
        self,
        aoi_model: SeplanAoi,
        benefit_model: cmod.BenefitModel,
        constraint_model: cmod.ConstraintModel,
        cost_model: cmod.CostModel,
    ):
        """A class to compute the different indices of seplan.

        We use a class instead of a comparaison to be able to compare multiple scenarios
        """
        # save the models as members
        self.aoi_model = aoi_model
        self.cost_model = cost_model
        self.benefit_model = benefit_model
        self.constraint_model = constraint_model

    def get_benefit_index(self, clip: bool = False) -> ee.Image:
        """Build the index exclusively on the benefits weighted approach."""
        # This is benefit sum

        # normalize all the benefit on the aoi
        aoi = self.aoi_model.feature_collection
        images = [
            _percentile(ee.Image(i).unmask(), aoi) for i in self.benefit_model.assets
        ]

        default = {"image": ee.Image(0), "weight": 0, "nb": 0}
        theme_images = {k: default.copy() for k in set(self.benefit_model.themes)}
        for idx, image in enumerate(images):
            theme_image = theme_images[self.benefit_model.themes[idx]]
            theme_image["image"] = theme_image["image"].add(image)
            theme_image["weight"] += self.benefit_model.weights[idx]
            theme_image["nb"] += 1

        for v in theme_images.values():
            v["weight"] = round(v["weight"] / v["nb"], 5)

        index = ee.Image(0)
        for v in theme_images.values():
            index = index.add(v["image"].divide(ee.Image(v["weight"])))
        index = _percentile(index, aoi)

        return index.clip(aoi) if clip is True else index

    def get_benefit_cost_index(self, clip: bool = False) -> ee.Image:
        """Build the benefit/cost ratio."""
        # This is 'benefit/cost ratio'

        # unmask the images without normalizing as everything is in $/ha
        aoi = self.aoi_model.feature_collection
        images = [ee.Image(i).unmask() for i in self.cost_model.assets]

        # create a normalized sum
        norm_cost = ee.Image(0)
        for v in images:
            norm_cost = norm_cost.add(v)
        norm_cost = _min_max(norm_cost, aoi)

        # create the benefits cost ratio
        index = self.get_benefit_index().divide(norm_cost)
        index = _percentile(index, aoi)

        return index.clip(aoi) if clip is True else index

    def get_constraint_index(self, clip: bool = False) -> ee.Image:
        aoi = self.aoi_model.feature_collection

        # create the mask from the constraints
        valid_data = ee.Image(0)
        for i, asset in enumerate(self.constraint_model.assets):
            # differentiate between different data types.

            data_type = self.constraint_model.data_type[i]
            values = self.constraint_model.values[i]
            image = ee.Image(asset).select(0).unmask()

            if data_type == "binary":
                # maskout images with model value
                valid_values = image.eq(values[0]).Not().selfMask()

            elif data_type == "categorical":
                valid_values = ee.List(values)
                new_vals = ee.List.repeat(1, valid_values.size())
                valid_values = image.remap(valid_values, new_vals, 0).selfMask()

            elif data_type == "continuous":
                min_, max_ = values
                valid_values = image.gt(max_).Or(image.lt(min_)).Not().selfMask()

            valid_data = valid_data.add(valid_values)

        valid_data = valid_data.gt(0).selfMask()

        index = _percentile(self.get_benefit_cost_index().mask(valid_data), aoi)

        return index.clip(aoi) if clip is True else index


def _percentile(
    ee_image: ee.Image,
    aoi: ee.FeatureCollection,
    scale: int = 10000,
    percentile: List[int] = [3, 97],
) -> ee.Image:
    """Return a normalized version of the layer image."""
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
    """Return a normalized version of the layer image."""
    ee_image = ee_image.select(0)
    min_max = ee_image.rename("img").reduceRegion(
        reducer=ee.Reducer.minMax(), geometry=aoi.geometry(), scale=scale
    )
    low = ee.Number(min_max.get("img_min"))
    high = ee.Number(min_max.get("img_max")).add(0.1e-13)

    return ee_image.unitScale(low, high).float()
