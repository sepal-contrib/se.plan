"""SE.PLAN model to store the data related with areas of interest."""

import json
from pathlib import Path
from typing import Tuple, Dict as DictType, Any as AnyType

import geopandas as gpd
import pygaul
from sepal_ui import color, model
from sepal_ui.aoi.aoi_model import AoiModel
from sepal_ui.message import ms
from sepal_ui.scripts import utils as su
from sepal_ui.scripts.gee_interface import GEEInterface
from traitlets import Dict, Int, Any


class AoiModel(AoiModel):
    updated = Int(0).tag(sync=True)
    """announces when the model is updated"""

    def __init__(self, gee_interface: GEEInterface = None, **kwargs):
        super().__init__(gee_interface=gee_interface, **kwargs)

        # set the default
        self.set_default(self.default_vector, self.default_admin, self.default_asset)

    def set_object(self, method: str = ""):
        """Set the object (gdf/featurecollection) based on the model inputs.

        The method can be manually overwritten by setting the ``method`` parameter.

        Args:
            method: a model loading method
        """
        # clear the model output if existing
        self.clear_output()

        # overwrite self.method
        self.method = method or self.method

        if self.method in ["ADMIN0", "ADMIN1", "ADMIN2"]:
            self._from_admin(self.admin)
        elif self.method == "POINTS":
            self._from_points(self.point_json)
        elif self.method == "SHAPE":
            self._from_vector(self.vector_json)
        elif self.method == "DRAW":
            self._from_geo_json(self.geo_json)
        elif self.method == "ASSET":
            self._from_asset(self.asset_json)
        else:
            raise Exception(ms.aoi_sel.exception.no_inputs)

        self.updated += 1

        return self

    async def set_object_async(self, method: str = ""):
        """Set the object (gdf/featurecollection) based on the model inputs.

        The method can be manually overwritten by setting the ``method`` parameter.

        Args:
            method: a model loading method
        """
        # clear the model output if existing
        self.clear_output()

        # overwrite self.method
        self.method = method or self.method

        if self.method in ["ADMIN0", "ADMIN1", "ADMIN2"]:
            await self._from_admin_async(self.admin)
        elif self.method == "SHAPE":
            await self._from_vector_async(self.vector_json)
        elif self.method == "DRAW":
            await self._from_geo_json_async(self.geo_json)
        elif self.method == "ASSET":
            self._from_asset(self.asset_json)
        else:
            raise Exception(ms.aoi_sel.exception.no_inputs)

        self.updated += 1

        return self

    def clear_attributes(self):
        """Return all attributes to their default state.

        Note:
            Set the default setting as current object.
        """
        # keep the default
        admin = self.default_admin
        vector = self.default_vector
        asset = self.default_asset

        # delete all the traits but the updated one (to avoid triggering the event)
        [
            setattr(self, attr, None)
            for attr in self.trait_names()
            if attr not in ["updated", "object_set"]
        ]

        # reset the outputs
        self.clear_output()

        # reset the default
        self.set_default(vector, admin, asset)

        # Tell seplan_aoi to update their linked traits (feature collecction)
        self.updated += 1

        return self

    async def _from_vector_async(self, vector_json: dict):
        """Set the object output from a vector json.

        Args:
            vector_json: the dict describing the vector file, and column filter
        """
        if not (vector_json["pathname"]):
            raise Exception(ms.aoi_sel.exception.no_file)

        if vector_json["column"] != "ALL":
            if vector_json["value"] is None:
                raise Exception(ms.aoi_sel.exception.no_value)

        # cast the pathname to pathlib Path
        vector_file = Path(vector_json["pathname"])

        # create the gdf
        self.gdf = gpd.read_file(vector_file).to_crs("EPSG:4326")

        # set the name using the file stem
        self.name = vector_file.stem

        # filter it if necessary
        if vector_json["value"] is not None:
            self.gdf = self.gdf[self.gdf[vector_json["column"]] == vector_json["value"]]
            self.name = f"{self.name}_{vector_json['column']}_{vector_json['value']}"

        if self.gee:
            # transform the gdf to ee.FeatureCollection
            self.feature_collection = su.geojson_to_ee(self.gdf.__geo_interface__)

            # export as a GEE asset
            await self.export_to_asset_async()

        return self

    async def _from_geo_json_async(self, geo_json: dict):
        """Set the gdf output from a geo_json.

        Args:
            geo_json: the __geo_interface__ dict of a geometry drawn on the map
        """
        if not geo_json:
            raise Exception(ms.aoi_sel.exception.no_draw)

        # remove the style property from geojson as it's not recognize by geopandas and gee
        for feat in geo_json["features"]:
            if "style" in feat["properties"]:
                del feat["properties"]["style"]

        # create the gdf
        self.gdf = gpd.GeoDataFrame.from_features(geo_json).set_crs(epsg=4326)

        # normalize the name
        self.name = su.normalize_str(self.name)

        if self.gee:
            # transform the gdf to ee.FeatureCollection
            self.feature_collection = su.geojson_to_ee(self.gdf.__geo_interface__)

            # export as a GEE asset
            await self.export_to_asset_async()
        else:
            # save the geojson in downloads
            path = Path("~", "downloads", "aoi").expanduser()
            path.mkdir(
                exist_ok=True, parents=True
            )  # if nothing have been run the downloads folder doesn't exist
            self.gdf.to_file(path / f"{self.name}.geojson", driver="GeoJSON")

        return self

    async def _from_admin_async(self, admin: str):
        """Set the object according to the given an administrative code in the GADM/GAUL codes.

        Args:
            admin: the admin code corresponding to FAO GAUl (if gee) or GADM
        """
        if not admin:
            raise Exception(ms.aoi_sel.exception.no_admlyr)

        # get the data from either the pygaul or the pygadm libs
        # pygaul needs extra work as ISO codes are not included in the GEE dataset
        self.feature_collection = pygaul.AdmItems(admin=admin)

        # get the ADM0_CODE to get the ISO code
        feature = self.feature_collection.first()
        properties = await self.gee_interface.get_info_async(
            feature.toDictionary(feature.propertyNames())
        )

        iso = json.loads(self.MAPPING.read_text())[str(properties.get("ADM0_CODE"))]
        names = [value for prop, value in properties.items() if "NAME" in prop]

        # generate the name from the columns
        names = [su.normalize_str(name) for name in names]
        names[0] = iso

        self.name = "_".join(names)

        return self


class SeplanAoi(model.Model):
    feature_collection = Any().tag(sync=True)
    """ee.FeatureCollection: feature collection representation of the aoi"""

    custom_layers = Dict({"type": "FeatureCollection", "features": []}).tag(sync=True)
    """dict: custom geometries drawn by the user. It's linked automatically with the map_.custom_layers"""

    set_map = Int(0).tag(sync=True)
    """int: This trait is listened by the custom AOI view, and will fire the btn"""

    reset_view = Int(0).tag(sync=True)
    """int: This trait is listened by the custom AOI view, and will reset the view"""

    updated = Int(0).tag(sync=True)
    """int: this trait will be updated every time the aoi_model is updated"""

    def __init__(self, gee_interface=None, **kwargs):
        # test_countries:
        # Multiple polygon country: 220
        # Small department: 959 (risaralda)
        # Medium department: 935 (Antioquia)
        self.aoi_model = AoiModel(gee_interface=gee_interface, **kwargs)

        self.aoi_model.observe(self.on_aoi_change, "updated")

    def on_aoi_change(self, change):
        """Update the feature_collection when the aoi_model.name is updated."""
        self.feature_collection = self.aoi_model.feature_collection
        self.updated += 1

    def get_ee_features(self) -> Tuple[DictType[str, AnyType], DictType[str, AnyType]]:
        """Returns a dictionary of current AOI layers, where name is the key."""
        primary_aoi = {
            self.aoi_model.name: {
                "ee_feature": self.feature_collection,
                "color": color.primary,
            }
        }

        custom_aois = {
            feat["properties"]["name"]: {
                "ee_feature": su.geojson_to_ee(feat),
                "color": feat["properties"]["style"]["color"],
            }
            for feat in self.custom_layers["features"]
        }

        return (primary_aoi, custom_aois)

    def import_data(self, data: dict, auto_update: bool = True):
        """Set the data for each of the AOIs."""
        # I need to reset the traits before importing the data
        # so they can trigger events if they've no changed.
        # self.reset()

        self.aoi_model.import_data(data["primary"])
        self.custom_layers = data["custom"]

        # if there's no aoi we just need to reset the map
        if not data["primary"]["method"]:
            self.reset_view += 1
            return

        self.set_map += 1

        if auto_update:
            self.aoi_model.set_object()

    async def import_data_async(self, data: dict, auto_update: bool = True):
        self.aoi_model.import_data(data["primary"])
        self.custom_layers = data["custom"]

        # if there's no aoi we just need to reset the map
        if not data["primary"]["method"]:
            self.reset_view += 1
            return

        self.set_map += 1

        if auto_update:
            await self.aoi_model.set_object_async()

    def export_data(self):
        """Save the data from each of the AOIs."""
        return {"primary": self.aoi_model.export_data(), "custom": self.custom_layers}

    def reset(self):
        """Reset the aoi_model to its default values."""
        self.aoi_model.clear_attributes()
        self.custom_layers = {"type": "FeatureCollection", "features": []}

        # I have to do this because I need to have an unique event on reset
        # that resets the view, We can use this event to reset the map as well...
        self.reset_view += 1
