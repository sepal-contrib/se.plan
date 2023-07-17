from copy import deepcopy

from sepal_ui import color as sc
from sepal_ui import sepalwidgets as sw

from component import parameter as cp
from component import scripts as cs
from component.message import cm
from component.scripts.seplan import Seplan
from component.widget.map import SeplanMap
from component.widget.map_toolbar import MapBar


class MapTile(sw.Layout):
    def __init__(self, seplan_model: Seplan, area_tile, theme_tile):
        self.attributes = {"_metadata": "map_widget"}
        self.class_ = "d-block"

        super().__init__()

        self.seplan_model = seplan_model

        title = sw.Html(tag="h2", children=[cm.map.title])
        description = sw.Markdown("  \n".join(cm.map.txt))

        self.colors = []
        self.alert = sw.Alert()
        self.map_ = SeplanMap()
        self.map_bar = MapBar(model=self.seplan_model, map_=self.map_)

        # get the dashboard tile
        self.area_tile = area_tile
        self.theme_tile = theme_tile

        # init the final layers
        self.wlc_outputs = None
        self.area_dashboard = None
        self.theme_dashboard = None

        self.children = [title, description, self.alert, self.map_bar, self.map_]

        # # decorate the function
        # self._compute = su.loading_button(self.alert, self.map_btn, debug=True)(
        #     self._compute
        # )
        # self._dashboard = su.loading_button(
        #     self.alert, self.compute_dashboard, debug=True
        # )(self._dashboard)

        # # add js behaviour
        # self.compute_dashboard.on_event("click", self._dashboard)
        # self.map_btn.on_event("click", self._compute)

    def _compute(self, widget, data, event):
        """compute the restoration plan and display the map."""
        # remove the previous sub aoi from the map
        self.m.remove_all()
        self.m.dc.clear()
        self.draw_features = deepcopy(self.EMPTY_FEATURES)

        # add the AOI geometry
        # using the color code of the dashboard
        style = {
            **cp.aoi_style,
            "fillOpacity": 0,
            "color": sc.primary,
            "fillColor": sc.primary,
        }
        aoi_layer = self.aoi_model.get_ipygeojson()
        aoi_layer.name = f"{self.aoi_model.name}"
        aoi_layer.style = style
        aoi_layer.hover_style = {**style, "weight": 2}
        aoi_layer.on_hover(self._display_name)
        self.m.add_layer(aoi_layer)

        # create a layer and a dashboard
        self.wlc_outputs = cs.wlc(
            self.layer_model.layer_list,
            self.question_model.constraints,
            self.question_model.priorities,
            self.aoi_model.feature_collection,
        )

        # display the layer in the map
        cs.display_layer(self.wlc_outputs[0], self.aoi_model, self.m)

        self.save.set_data(
            self.wlc_outputs[0],
            self.aoi_model.feature_collection.geometry(),
            self.question_model.recipe_name,
            self.aoi_model.name,
        )

        # add the possiblity to draw on the map and release the compute dashboard btn
        self.m.show_dc()

        # enable the dashboard computation
        self.compute_dashboard.disabled = False

        return self

    def _dashboard(self, widget, data, event):
        # handle the drawing features, affect them with a color an display them on the map as layers
        self._save_features()

        # create a name list
        names = [self.aoi_model.name] + [
            feat["properties"]["name"] for feat in self.draw_features["features"]
        ]

        # retreive the area and theme json result
        self.area_dashboard, self.theme_dashboard = cs.get_stats(
            self.wlc_outputs,
            self.layer_model,
            self.aoi_model,
            self.draw_features,
            names,
        )

        # save the dashboard as a csv
        cs.export_as_csv(
            self.area_dashboard,
            self.theme_dashboard,
            self.aoi_model.name,
            self.question_model.recipe_name,
        )

        # set the content of the panels
        self.theme_tile.dev_set_summary(self.theme_dashboard, names, self.colors)
        self.area_tile.set_summary(self.area_dashboard)

        return self
