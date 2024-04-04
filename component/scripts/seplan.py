"""All tools to build the suitability index."""

from typing import List, Literal, Tuple, Union

import ee

from component import model as cmod
from component.message import cm
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

    def get_benefit_index(self, clip: bool = True) -> ee.Image:
        """Build the index exclusively on the benefits weighted approach."""
        aoi = self.aoi_model.feature_collection

        if not aoi:
            raise ValueError(cm.map.error.no_aoi)

        # decompose benefit list to get only the image
        normalize_benefits = [
            quintiles(image, aoi) for image, _ in self.get_benefits_list()
        ]

        index = get_weighted_average(
            self.benefit_model.themes, normalize_benefits, self.benefit_model.weights
        )

        return index.clip(aoi) if clip is True else index

    def get_benefit_cost_index(self, clip: bool = True) -> ee.Image:
        """Build the benefit/cost ratio."""
        # This is 'benefit/cost ratio'

        # unmask the images without normalizing as everything is in $/ha
        aoi = self.aoi_model.feature_collection
        images = [ee.Image(i) for i in self.cost_model.assets]

        # create a normalized sum
        norm_cost = ee.Image(0)
        for v in images:
            norm_cost = norm_cost.add(v)

        # TODO: check if this is the best way to normalize
        # norm_cost = _min_max(norm_cost, aoi)

        # create the benefits cost ratio
        index = self.get_benefit_index(clip=clip).divide(norm_cost)
        index = _percentile(index, aoi)

        return index.clip(aoi) if clip is True else index

    def get_constraint_index(self, clip: bool = True) -> ee.Image:
        """Get suitability index masked with constraints."""
        aoi = self.aoi_model.feature_collection
        mask_out_areas = reduce_constraints(self.get_masked_constraints_list())

        index = (
            self.get_benefit_cost_index(clip=clip)
            .multiply(4)
            .add(1)
            .mask(mask_out_areas)
            .unmask(0)
        )

        return index.clip(aoi) if clip is True else index

    def get_benefits_list(self) -> List[Tuple[ee.Image, str]]:
        """Returns a list of named ee_image benefits from user input."""
        return [
            [ee.Image(asset), self.benefit_model.ids[i]]
            for i, asset in enumerate(self.benefit_model.assets)
        ]

    def get_costs_list(self) -> List[Tuple[ee.Image, str]]:
        """Returns a list of named costs ee.Images from user input."""
        return [
            [ee.Image(asset), self.cost_model.ids[i]]
            for i, asset in enumerate(self.cost_model.assets)
        ]

    def get_masked_constraints_list(self) -> List[Tuple[ee.Image, str]]:
        """Returns a list of named constraints masks from user input."""
        # create the mask from the constraints
        masked_data = []
        for i, asset in enumerate(self.constraint_model.assets):
            # differentiate between different data types.

            data_type = self.constraint_model.data_type[i]
            values = self.constraint_model.values[i]

            masked_image = mask_image(asset, data_type, values)

            # set the name of the image as a property of the image
            masked_data.append(
                [masked_image.rename("mask"), self.constraint_model.ids[i]]
            )

        return masked_data


def asset_to_image(asset_id: str) -> ee.Image:
    """Convert an asset to an image."""
    return ee.Image(asset_id).select(0).selfMask()


def mask_image(
    asset_id: str,
    data_type: Literal["binary", "categorical", "continuous"],
    maskout_values: list,
) -> ee.Image:
    """Mask out an image based on its data type and input values."""
    image = ee.Image(asset_id).select(0).unmask()

    if data_type == "binary":
        # mask out image values that are equal to user's input
        return image.eq(maskout_values[0]).Not().selfMask()

    elif data_type == "categorical":
        to_mask_values = ee.List(maskout_values)
        mask_value = ee.List.repeat(0, to_mask_values.size())
        return image.remap(to_mask_values, mask_value, 1).selfMask()

    elif data_type == "continuous":
        min_, max_ = maskout_values
        return image.gt(min_).And(image.lt(max_)).Not().selfMask()


def reduce_constraints(masked_constraints_list: List[Tuple[ee.Image, str]]) -> ee.Image:
    """Reduce constraints list and returns one image masked."""
    constraints = [constraint for constraint, _ in masked_constraints_list]
    return ee.Image(constraints).mask().reduce(ee.Reducer.min()).gt(0).selfMask()


def _percentile(
    ee_image: ee.Image,
    aoi: ee.FeatureCollection,
    scale: int = 10000,
    percentile: Tuple[int, int] = [3, 97],
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


def get_weighted_average(
    themes: List[str], images: List[ee.Image], weights: List[float]
) -> ee.Image:
    """Creates a weighted average of images based on a list of weights.

    Note that images and weights must be in the same order.
    """
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


def quintiles(
    ee_image: ee.Image, ee_aoi: Union[ee.FeatureCollection, ee.Geometry]
) -> ee.Image:
    """Return a normalized quintile image of the input image over the aoi."""
    # ee_image.projection().nominalScale().multiply(2)

    band_name = ee.String(ee_image.bandNames().get(0))
    quintiles_dict = ee_image.reduceRegion(
        reducer=ee.Reducer.percentile(percentiles=[20, 40, 60, 80]),
        geometry=ee_aoi,
        tileScale=2,
        scale=100,
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
        .where(ee_image.gt(0).And(ee_image.lte(low)), 1)
        .where(ee_image.gt(low).And(ee_image.lte(lowmed)), 2)
        .where(ee_image.gt(lowmed).And(ee_image.lte(highmed)), 3)
        .where(ee_image.gt(highmed).And(ee_image.lte(high)), 4)
        .where(ee_image.gt(high), 5)
    ).selfMask()
