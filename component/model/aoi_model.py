"""SE.PLAN model to store the data related with areas of interest."""
from sepal_ui import color, model
from sepal_ui.aoi.aoi_model import AoiModel
from sepal_ui.scripts import utils as su
from traitlets import Any, Dict, Unicode, link, observe


class SeplanAoi(model.Model):
    feature_collection = Any().tag(sync=True)
    """ee.FeatureCollection: feature collection representation of the aoi"""

    custom_layers = Dict({"type": "FeatureCollection", "features": []}).tag(sync=True)
    """dict: custom geometries drawn by the user. It's linked automatically with the map_.custom_layers"""

    name = Unicode("", allow_none=True).tag(sync=True)
    """str: given name from aoi.model to the aoi"""

    def __init__(self):
        # test_countries:
        # Multiple polygon country: 220
        # Small department: 959 (risaralda)
        # Medium department: 935 (Antioquia)
        self.aoi_model = AoiModel(admin="935")

        # As the feature colleciton from model is not a trait, we need to link something that changes when model is updated, that's the name
        link((self.aoi_model, "name"), (self, "name"))

    @observe("name")
    def on_aoi_change(self, change):
        """Update the feature_collection when the aoi_model.name is updated."""
        self.feature_collection = self.aoi_model.feature_collection

    def get_ee_features(self) -> Dict:
        """Returns a dictionary of current AOI layers, where name is the key."""
        primary_aoi = {
            self.name: {
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

    def load_data(self, data: dict):
        """Set the data for each of the AOIs."""
        self.aoi_model.load_data(data["primary"])
        self.custom_layers = data["custom"]

    def export_data(self):
        """Save the data from each of the AOIs."""
        return {"primary": self.aoi_model.save_data(), "custom": self.custom_layers}
