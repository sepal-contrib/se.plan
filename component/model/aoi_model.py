"""SE.PLAN model to store the data related with areas of interest."""
from sepal_ui import color, model
from sepal_ui.aoi.aoi_model import AoiModel
from sepal_ui.message import ms
from sepal_ui.scripts import utils as su
from traitlets import Any, Dict, Int


class AoiModel(AoiModel):
    updated = Int(0).tag(sync=True)
    """announces when the model is updated"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        [setattr(self, attr, None) for attr in self.trait_names() if attr != "updated"]

        # reset the outputs
        self.clear_output()

        # reset the default
        self.set_default(vector, admin, asset)

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

    def __init__(self, **kwargs):
        # test_countries:
        # Multiple polygon country: 220
        # Small department: 959 (risaralda)
        # Medium department: 935 (Antioquia)
        self.aoi_model = AoiModel(**kwargs)

        self.aoi_model.observe(self.on_aoi_change, "updated")

    def on_aoi_change(self, change):
        """Update the feature_collection when the aoi_model.name is updated."""
        self.feature_collection = self.aoi_model.feature_collection
        self.updated += 1

    def get_ee_features(self) -> Dict:
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

        return {**primary_aoi, **custom_aois}

    def import_data(self, data: dict):
        """Set the data for each of the AOIs."""
        # I need to reset the traits before importing the data
        # so they can trigger events if they've no changed.
        # self.reset()

        self.aoi_model.import_data(data["primary"])
        self.custom_layers = data["custom"]

        self.set_map += 1

    def export_data(self):
        """Save the data from each of the AOIs."""
        return {"primary": self.aoi_model.export_data(), "custom": self.custom_layers}

    def reset(self):
        """Reset the aoi_model to its default values."""
        self.aoi_model.clear_output()
        self.custom_layers = {"type": "FeatureCollection", "features": []}

        # I have to do this because I need to have an unique event on reset
        # that resets the view as well
        self.reset_view += 1
