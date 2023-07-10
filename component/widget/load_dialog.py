import geopandas as gpd
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component.message import cm


class LoadDialog(sw.Dialog):
    def __init__(self):
        self.class_ = "mb-5 mt-2"
        self.v_model = False
        self.max_width = "700px"

        super().__init__()

        # add a btn to click
        self.btn = sw.Btn(
            cm.map.shapes.btn, icon="mdi-download", class_="ml-2", small=True
        )

        # and the vector selector
        self.w_vector = CustomVector(label=cm.map.shapes.file)

        # create an alert for the su.loading_button
        self.alert = sw.Alert()

        # generate the panels
        title = sw.CardTitle(children=[cm.map.shapes.title])
        text = sw.CardText(children=[self.w_vector, self.alert])
        actions = sw.CardActions(children=[sw.Spacer(), self.btn])

        self.children = [sw.Card(children=[title, text, actions])]

    def open_dialog(self, *_):
        """Open dialog."""
        self.v_model = True

    @su.loading_button(debug=False)
    def read_data(self):
        # extract information for compacity
        value = self.w_vector.v_model["value"]
        column = self.w_vector.v_model["column"]
        pathname = self.w_vector.v_model["pathname"]

        if column in ["ALL", None]:
            raise Exception("Please select data")

        # create the gdf and filter if necessary
        gdf = gpd.read_file(pathname)
        gdf = gdf if value is None else gdf[gdf[column] == value]

        return gdf, column


class CustomVector(sw.VectorField):
    def _update_file(self, change):
        """remove the select 'all feature' option as feature is used to name the AOIs."""

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.w_column.v_model = None
            self.w_column.items = None

        super()._update_file(change)

        # update the columns
        self.w_column.v_model = None
        self.w_column.items = self.w_column.items[1:]

        return self
