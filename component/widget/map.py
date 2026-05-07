import time
from copy import deepcopy
from typing import Optional

import ipyvuetify as v
from component.frontend.icons import icon
from component.widget.buttons import IconBtn, TextBtn
import sepal_ui.sepalwidgets as sw
from ipyleaflet import GeoJSON, WidgetControl, basemap_to_tiles, basemaps
from shapely.geometry import Point, shape
from sepal_ui import mapping as sm
from traitlets import Dict, Int, link
from sepal_ui.scripts.gee_interface import GEEInterface
from sepal_ui import color
from sepal_ui.mapping.map_btn import MapBtn
from component.widget.admin_aoi_dialog import AdminAoiDialog
from component.widget.custom_geometries_dialog import CustomGeometriesDialog
from component.message import cm
from component import widget as cw

from component.model.aoi_model import SeplanAoi
from component.widget.admin_aoi_dialog import _is_admin_eligible
from ipyleaflet import SplitMapControl


class SeplanMap(sm.SepalMap):
    custom_layers = Dict({"type": "FeatureCollection", "features": []}).tag(sync=True)
    "dict: custom geometries drawn by the user"

    new_geom = Int(0).tag(sync=True)
    """int: either a new geometry has been drawn on the map"""

    def __init__(
        self,
        seplan_aoi: SeplanAoi = None,
        theme_toggle=None,
        gee_interface: GEEInterface = None,
        *args,
        **kwargs,
    ):
        self.aoi_model = seplan_aoi if seplan_aoi else SeplanAoi()

        self.attributes = {"id": "map"}

        super().__init__(
            theme_toggle=theme_toggle,
            gee_interface=gee_interface,
            fullscreen=True,
            *args,
            **kwargs,
        )
        # self.dc = True
        self.vinspector = True
        self.min_zoom = 3
        self.add_basemap("SATELLITE")
        self.dc.hide()

        # Single right-panel entry point that opens the consolidated modal.
        # The actual Admin / Draw / Import items live inside that modal as
        # list items (see ``custom_geometries_dialog.CustomGeometriesDialog``).
        self.btn_custom_geom = TextBtn(
            "Custom geometries",
            block=True,
            disabled=True,
        )

        self.btn_clean = MapBtn(icon("broom"))

        self.custom_aoi_dialog = cw.CustomAoiDialog(self)
        self.import_aoi_dialog = cw.ImportAoiDialog(
            self.custom_aoi_dialog, gee_interface=self.gee_interface
        )

        self.admin_aoi_dialog = AdminAoiDialog(
            custom_aoi_dialog=self.custom_aoi_dialog,
            gee_interface=self.gee_interface,
            map_=self,
        )
        self.custom_geometries_dialog = CustomGeometriesDialog(self)

        # The suitability legend is now mounted as a Solara overlay in Page()
        # via component.widget.seplan_legend.SuitabilityLegendOverlay.

        # create a window to display AOI information
        self.html = sw.Html(tag="h3", style_="margin:0em 2em 0em 2em;")
        control = WidgetControl(widget=self.html, position="bottomright")
        self.add(control)

        # btn_custom_geom lives in the right panel and opens
        # ``custom_geometries_dialog``, which renders the action list items
        # and the saved-geometries table.
        self.add(WidgetControl(widget=self.btn_clean, position="topright"))
        self.add(WidgetControl(widget=self.custom_aoi_dialog, position="topright"))
        self.add(WidgetControl(widget=self.import_aoi_dialog, position="topright"))
        self.add(WidgetControl(widget=self.admin_aoi_dialog, position="topright"))
        self.add(
            WidgetControl(widget=self.custom_geometries_dialog, position="topright")
        )

        # Cached (minx, miny, maxx, maxy, shapely_geom) per custom layer for
        # the cheap hover-leave detection — rebuilt only when ``custom_layers``
        # changes (not on every mousemove).
        self._hover_bbox_cache: list = []
        self._hover_check_last: float = 0.0

        self.dc.on_draw(self._handle_draw)
        self.observe(self.on_custom_layers, "custom_layers")
        self.on_interaction(self._on_map_interaction)

        # It has to be two way, so we can load the data by just updating the model
        link((self, "custom_layers"), (self.aoi_model, "custom_layers"))

        self.aoi_model.observe(self.reset, "reset_view")

        # Click dispatch on the modal's list items is wired inside
        # ``CustomGeometriesDialog._make_list_item`` (each item registers
        # ``self.map_.on_draw`` as its click handler).
        self.btn_clean.on_event("click", self.clean_map)
        self.btn_custom_geom.on_event(
            "click", lambda *_: self.custom_geometries_dialog.open_dialog()
        )

        # Enable the entry button + modal items only once a primary AOI exists.
        self._sync_custom_geom_buttons()
        self.aoi_model.observe(self._sync_custom_geom_buttons, "feature_collection")
        # Admin sub-area also depends on the primary AOI's method, which only
        # changes via the inner ``aoi_model`` (e.g. ``ADMIN0`` → ``DRAW``).
        self.aoi_model.aoi_model.observe(self._sync_custom_geom_buttons, "method")

    def _sync_custom_geom_buttons(self, *_):
        """Toggle the entry button + modal list items based on the primary AOI.

        Sub-AOIs only make sense relative to a defined primary AOI, so the
        ``Custom geometries`` entry button and the Draw / Import items inside
        its modal stay disabled until ``seplan_aoi.feature_collection`` is set.
        The Admin sub-area item has an extra constraint: it only makes sense
        when the primary AOI is admin-based (``ADMIN0`` or ``ADMIN1``);
        ``ADMIN2`` is the finest grain so no further subdivision is offered,
        and non-admin primaries (DRAW / SHAPE / ASSET) skip it.
        """

        has_aoi = self.aoi_model.feature_collection is not None
        primary_method = getattr(self.aoi_model.aoi_model, "method", "") or ""
        admin_eligible = has_aoi and _is_admin_eligible(primary_method)

        self.btn_custom_geom.disabled = not has_aoi

        dialog = getattr(self, "custom_geometries_dialog", None)
        if dialog is not None:
            dialog.item_new.disabled = not has_aoi
            dialog.item_import.disabled = not has_aoi
            dialog.item_admin.disabled = not admin_eligible

    def on_draw(self, widget, event, data):
        """Dispatch list-item clicks from the Custom Geometries modal.

        Closes the picker first so the user lands directly on the chosen
        surface. For Import / Admin we also pass ``return_to`` so a Cancel
        click in those dialogs walks the user back to the picker rather
        than dropping them on the bare map.
        """
        self.custom_geometries_dialog.close_dialog()

        if widget.attributes["id"] == "new":
            self.dc.show()

        elif widget.attributes["id"] == "import":
            self.dc.hide()
            self.import_aoi_dialog.open_dialog(return_to=self.custom_geometries_dialog)

        elif widget.attributes["id"] == "admin":
            self.dc.hide()
            self.admin_aoi_dialog.open_dialog(return_to=self.custom_geometries_dialog)

    def clean_map(self, *args, keep_aoi: bool = True):
        """Remove computed result layers but keep the AOI and user geometries.

        Custom sub-AOIs the user drew or imported live in
        ``self.custom_layers``; their on-map ipyleaflet ``GeoJSON`` layers
        carry the user's chosen names. We preserve those by name so that
        re-running compute / compare-scenarios doesn't wipe them.
        """
        keep = ["aoi"] if keep_aoi else []
        keep += [
            feat["properties"]["name"]
            for feat in self.custom_layers["features"]
            if feat.get("properties", {}).get("name")
        ]
        self.remove_all(keep_names=keep)
        self.controls = [
            control
            for control in self.controls
            if not isinstance(control, SplitMapControl)
        ]

    def on_custom_layers(self, *_):
        """Event triggered when there are new custom layers (created by user).

        Create GeoJSON layers and add them to the map if they're not.

        """
        geojson_layers = [layer for layer in self.layers if isinstance(layer, GeoJSON)]
        # Check if there are new geometries in the custom_layers
        # If there are new geometries that are not in the map, add them

        # Add layers to the map
        for feat in self.custom_layers["features"]:
            if feat["properties"]["name"] not in [lyr.name for lyr in geojson_layers]:
                # Add the layer to the map
                layer = GeoJSON(
                    data=feat,
                    hover_style=feat["properties"]["hover_style"],
                    name=feat["properties"]["name"],
                    style=feat["properties"]["style"],
                )
                layer.on_hover(self._display_name)

                # Add the layer to the map_layers list
                self.add_layer(layer)

        # Remove layers from the map
        for layer in geojson_layers:
            if layer.name not in [
                feat["properties"]["name"] for feat in self.custom_layers["features"]
            ]:
                self.remove_layer(layer)

        # Refresh the cached bbox / shapely geoms used by the hover-leave
        # detector. Built once here, not on every mousemove.
        cache = []
        for feat in self.custom_layers["features"]:
            geom_dict = feat.get("geometry")
            if not geom_dict:
                continue
            geom = shape(geom_dict)
            minx, miny, maxx, maxy = geom.bounds
            cache.append((minx, miny, maxx, maxy, geom))
        self._hover_bbox_cache = cache

    def remove_custom_layer(self, layer_id):
        """Remove custom layer from the custom_layers dict."""
        # Create a copy of the current custom_layers dict
        current_feats = deepcopy(self.custom_layers)

        # Search the layer_id in the custom_layers dict
        for feat in current_feats["features"]:
            if feat["properties"]["id"] == layer_id:
                current_feats["features"].remove(feat)

                # Trigger the change in the custom_layers dict
                self.custom_layers = current_feats

    def _handle_draw(self, target, action, geo_json):
        """handle the draw on map event.

        Accepts both action conventions — legacy ipl.DrawControl emits
        ``created``/``deleted``/``edited`` with ``geo_json`` as a single
        feature dict; Geoman emits ``create``/``remove``/``edit``/``cut``/
        ``rotate``/``vertexadded`` with ``geo_json`` as a list of features.
        We don't read ``geo_json`` here, so the shape difference is
        invisible at this layer. Polygonization happens at save time via
        ``self.dc.to_json()``.
        """
        if action in ("create", "created"):
            # custom_aoi_dialog will be listening to this trait
            self.new_geom += 1
            self.aoi_model.updated += 1

    def _on_map_interaction(self, **kwargs):
        """Clear the hover label when the cursor isn't over a custom layer.

        Mousemove fires constantly, so this runs on a multi-user server —
        we keep it cheap with three gates:

        1. ``self.html.children`` is empty → return immediately (no label
           to clear). This is the common case: the label only exists for
           a few seconds after a hover.
        2. Throttle to ~10 Hz via ``_hover_check_last``.
        3. Bounding-box quick-reject against the cached
           ``_hover_bbox_cache`` before paying for ``shapely.contains``.

        ``mouseout`` would be the natural signal but ipyleaflet's GeoJSON
        only registers ``mouseover``/``click`` on the JS side
        (``onEachFeature`` in jupyter-leaflet's index.js), so the comm
        never sees it.
        """
        if not self.html.children:
            return
        if kwargs.get("type") != "mousemove":
            return
        now = time.monotonic()
        if now - self._hover_check_last < 0.1:
            return
        self._hover_check_last = now
        coords = kwargs.get("coordinates")
        if not coords:
            return
        # Leaflet gives ``[lat, lng]``; shapely uses ``(x=lng, y=lat)``.
        x, y = coords[1], coords[0]
        for minx, miny, maxx, maxy, geom in self._hover_bbox_cache:
            if minx <= x <= maxx and miny <= y <= maxy:
                if geom.contains(Point(x, y)):
                    return
        self.html.children = []

    def _display_name(self, feature, **kwargs):
        """update the AOI in the html viewver widget."""
        # if the feature is a aoi it has no name so I display only the sub AOI name
        # it will be solved with: https://github.com/12rambau/sepal_ui/issues/390
        name = (
            feature["properties"]["name"]
            if "name" in feature["properties"]
            else "Main AOI"
        )
        self.html.children = [name]

        return self

    def reset(self, change):
        """Reset the map view (remove all the layers)."""
        self.center = [0, 0]
        self.zoom = 3
        self.remove_all()
