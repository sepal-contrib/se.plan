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
        aoi = self.aoi_model.feature_collection
        benefit_list = self.get_benefits_list()

        index = self.get_weighted_benefits(
            self.benefit_model.themes, benefit_list, self.benefit_model.weights
        )

        # TODO: I'm not really sure why do we need to calculate the _percentile here
        # but it's ok for now
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

        constraint_mask_list = self.get_constraint_mask_list()
        constraint_mask = (
            ee.ImageCollection(constraint_mask_list)
            .reduce(ee.Reducer.sum())
            .gt(0)
            .selfMask()
        )
        index = _percentile(self.get_benefit_cost_index().mask(constraint_mask), aoi)

        return index.clip(aoi) if clip is True else index

    def get_benefits_list(self) -> List[ee.Image]:
        """Returns a list of normalized benefits."""
        return [
            _percentile(ee.Image(i).unmask(), self.aoi_model.feature_collection)
            for i in self.benefit_model.assets
        ]

    def get_costs_list(self) -> List[ee.Image]:
        """Returns a list of normalized costs."""
        return [ee.Image(image).unmask() for image in self.cost_model.assets]

    def get_constraints_list(self, single=False) -> List[ee.Image]:
        """Returns constraint mask for the aoi, if single is True, returns a list of masks for each constraint."""
        # create the mask from the constraints
        valid_data = []
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

            valid_data.append(valid_values)

        return valid_data


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


def get_weighted_average(themes, images, weights) -> ee.Image:
    """Creates a weighted average of images based on their weights."""
    # Create an empty dictionary with the themes as keys
    default = {"image": ee.Image(0), "weight": 0, "nb": 0}
    theme_images = {k: default.copy() for k in set(themes)}

    for idx, image in enumerate(images):
        #  Get the theme of the image by the index of the asset
        theme_image = theme_images[themes[idx]]
        theme_image["image"] = theme_image["image"].add(image)
        theme_image["weight"] += weights[idx]
        theme_image["nb"] += 1

    for v in theme_images.values():
        # For those themes with multiple images, we get the simple average
        # in both the image and the weight
        v["image"] = v["image"].divide(v["nb"])
        v["weight"] = round(v["weight"] / v["nb"], 5)

    total_weight = sum([v["weight"] for v in theme_images.values()])

    weighted_image = ee.Image(0)
    for v in theme_images.values():
        # Get the weighted image by multiplying the image by the weight
        weighted_theme = v["image"].multiply(ee.Image(v["weight"]).divide(total_weight))

        # Add the weighted image
        weighted_image = weighted_image.add(weighted_theme)

    return weighted_image


def get_quintiles(ee_image: ee.Image, ee_aoi) -> ee.Image:
    scale = ee_image.projection().nominalScale().multiply(2)

    band_name = ee.String(ee_image.bandNames().get(0))
    quintiles_dict = ee_image.reduceRegion(
        reducer=ee.Reducer.percentile(percentiles=[20, 40, 60, 80]),
        geometry=ee_aoi,
        tileScale=2,
        scale=scale,
        maxPixels=1e13,
    )

    quintiles_names = ee.List(["p20", "p40", "p60", "p80"]).map(
        lambda quintile_name: band_name.cat("_").cat(ee.String(quintile_name))
    )

    low = ee.Number(quintiles_dict.get(quintiles_names.get(0)))
    lowmed = ee.Number(quintiles_dict.get(quintiles_names.get(1)))
    highmed = ee.Number(quintiles_dict.get(quintiles_names.get(2)))
    high = ee.Number(quintiles_dict.get(quintiles_names.get(3)))

    return (
        ee.Image(0)
        .where(ee_image.lte(low), 1)
        .where(ee_image.gt(low).And(ee_image.lte(lowmed)), 2)
        .where(ee_image.gt(lowmed).And(ee_image.lte(highmed)), 3)
        .where(ee_image.gt(highmed).And(ee_image.lte(high)), 4)
        .where(ee_image.gt(high), 5)
    )
