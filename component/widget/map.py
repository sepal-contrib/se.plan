import logging
import time
from copy import deepcopy
from functools import partial

import ee
import sepal_ui.sepalwidgets as sw
from ipyleaflet import SplitMapControl, WidgetControl
from sepal_ui import mapping as sm
from sepal_ui.mapping.map_btn import MapBtn
from sepal_ui.scripts.gee_interface import GEEInterface
from shapely.geometry import Point, shape
from traitlets import Dict, Int, link

from component import widget as cw
from component.frontend.icons import icon
from component.model.aoi_model import SeplanAoi
from component.scripts.aoi_geometry import _aoi_bbox, fc_from_source
from component.widget.admin_aoi_dialog import AdminAoiDialog, _is_admin_eligible
from component.widget.buttons import TextBtn
from component.widget.custom_geometries_dialog import CustomGeometriesDialog

logger = logging.getLogger("SEPLAN")


class SeplanMap(sm.SepalMap):
    custom_layers = Dict({"type": "FeatureCollection", "features": []}).tag(sync=True)
    "dict: custom geometries drawn by the user"

    new_geom = Int(0).tag(sync=True)
    """int: either a new geometry has been drawn on the map"""

    # Minimum seconds between hover-label recomputes in ``_on_map_interaction``.
    # mousemove fires constantly and this runs on the shared kernel; throttling
    # caps the per-user work. Higher = cheaper but laggier label (see ~5 Hz here).
    _HOVER_THROTTLE_S = 0.2

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

        # Custom-outline tile task + monotonic token (single-flight; a superseded
        # getMapId must not resurrect deleted outlines — see _refresh_outline_tiles).
        self._outline_task = None
        self._outline_gen = 0

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

        Custom sub-AOIs the user drew or imported are drawn as one merged EE
        tile layer (``_OUTLINE_KEY``); we preserve it (and the primary ``aoi``)
        so re-running compute / compare-scenarios doesn't wipe them.
        """
        keep = ["aoi"] if keep_aoi else []
        keep.append(self._OUTLINE_KEY)
        self.remove_all(keep_names=keep)
        self.controls = [
            control
            for control in self.controls
            if not isinstance(control, SplitMapControl)
        ]

    # Key of the single EE tile layer that draws all sub-AOI exact outlines.
    _OUTLINE_KEY = "custom_outlines"

    def on_custom_layers(self, *_):
        """Render custom sub-AOIs as pixel-perfect EE-tile outlines.

        There is deliberately NO client-side GeoJSON layer: the simplified
        display geometry can contain Point / LineString / GeometryCollection
        parts (small features collapse under simplification), which ipyleaflet
        renders as stray markers and which also break hover. Instead the exact
        outline is an EE tile layer and the name label is driven by
        ``_on_map_interaction`` against the per-sub-AOI geometry cache below.
        """
        features = self.custom_layers["features"]

        # exact outline tiles (single merged EE layer, rebuilt async)
        self._refresh_outline_tiles(features)

        # (bbox, shapely geom, name) per sub-AOI — drives the hover label.
        # ``shape`` handles every geometry type (incl. GeometryCollection); a
        # collapsed point/line part simply never ``contains`` the cursor.
        cache = []
        for feat in features:
            geom_dict = feat.get("geometry")
            name = feat.get("properties", {}).get("name")
            if not geom_dict or not name:
                continue
            try:
                geom = shape(geom_dict)
                minx, miny, maxx, maxy = geom.bounds
            except Exception:
                continue
            cache.append((minx, miny, maxx, maxy, geom, name))
        self._hover_bbox_cache = cache

    def _refresh_outline_tiles(self, features):
        """(Re)build the single EE tile layer with every sub-AOI's exact outline.

        The exact geometry is reconstructed server-side from each feature's
        ``source`` descriptor; the ``getMapId`` runs on the GEE event loop so the
        kernel thread stays responsive. Nothing dense is pulled to the client.

        Concurrency: bump a token and cancel the prior task BEFORE any layer
        mutation (incl. the empty/delete-all remove), so a slow ``getMapId`` from
        a superseded refresh can't resurrect deleted outlines.
        """
        if self._outline_task is not None:
            self._outline_task.cancel()
        self._outline_gen += 1
        my_gen = self._outline_gen

        if not features:
            self.remove_layer(self._OUTLINE_KEY, none_ok=True)
            return

        gee_interface = getattr(self, "gee_interface", None)
        if gee_interface is None:
            return

        # snapshot (the trait can change before the task runs)
        snapshot = [dict(f) for f in features]
        self._outline_task = gee_interface.create_task(
            func=partial(self._build_outline_tiles, snapshot, my_gen),
            key="custom_outline_tiles",
            on_error=lambda exc: logger.exception(
                "Custom outline tiles failed", exc_info=exc
            ),
        )
        self._outline_task.start()

    async def _build_outline_tiles(self, features, my_gen):
        """Merge each sub-AOI's exact FC, style per-feature, add as one tile layer."""
        if my_gen != self._outline_gen:  # superseded before we started
            return
        styled = []
        for feat in features:
            fc = fc_from_source(feat["properties"].get("source"), feat)
            color = feat["properties"]["style"]["color"]
            # per-feature style dict consumed by FeatureCollection.style(styleProperty)
            style_dict = {"color": color, "fillColor": "#00000000", "width": 2}
            styled.append(fc.map(lambda f, s=style_dict: f.set("_seplan_style", s)))

        merged = ee.FeatureCollection(styled).flatten()
        image = merged.style(styleProperty="_seplan_style")

        if my_gen != self._outline_gen:  # superseded while building the request
            return
        # add_layer self-removes the existing _OUTLINE_KEY layer; we deliberately
        # do NOT remove first (a stale task removing could blank a newer layer).
        await self.add_ee_layer_async(
            image, {}, self._OUTLINE_KEY, key=self._OUTLINE_KEY
        )

        # Delete-all guard: if every sub-AOI was removed while our getMapId was in
        # flight, drop the outline we just added (no clobber — only fires when the
        # map is genuinely empty).
        if not self.custom_layers["features"]:
            self.remove_layer(self._OUTLINE_KEY, none_ok=True)

    def zoom_to_custom(self, features: list) -> None:
        """Zoom to just-added custom sub-AOI feature(s) — async, off the kernel thread.

        Uses each feature's EXACT geometry (rebuilt from its ``source``
        descriptor) and per-feature bounding boxes (no dissolve), so it stays
        cheap and safe on dense AOIs. No-op without a GEE session or features.
        """
        gee_interface = getattr(self, "gee_interface", None)
        if gee_interface is None or not features:
            return
        snapshot = [dict(f) for f in features]
        self._zoom_custom_task = gee_interface.create_task(
            func=partial(self._zoom_to_custom_async, snapshot),
            key="custom_zoom",
            on_error=lambda exc: logger.exception("Custom zoom failed", exc_info=exc),
        )
        self._zoom_custom_task.start()

    async def _zoom_to_custom_async(self, features: list) -> None:
        """Resolve the added sub-AOI extent off the kernel thread and zoom to it."""
        fcs = [
            fc_from_source(feat.get("properties", {}).get("source"), feat)
            for feat in features
        ]
        merged = ee.FeatureCollection(fcs).flatten()
        # per-feature bbox (see _aoi_bbox) -> overall extent ring -> [minx,miny,maxx,maxy]
        coords = await self.gee_interface.get_info_async(
            _aoi_bbox(merged).coordinates().get(0)
        )
        bounds = [coords[0][0], coords[0][1], coords[2][0], coords[2][1]]
        self.zoom_bounds(bounds)

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
        """Handle the draw on map event.

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
        """Show/clear the sub-AOI name label from the cursor position.

        The custom outlines are EE tiles (raster, no per-feature events), so the
        label is driven here: on each (throttled) mousemove we find the sub-AOI
        whose cached geometry contains the cursor and show its name, clearing the
        label otherwise. A bbox quick-reject keeps the common case cheap.

        Mousemove fires constantly (multi-user server), so we gate on the
        ``_HOVER_THROTTLE_S`` throttle and a bounding-box reject before paying for
        ``shapely.contains``.
        """
        if kwargs.get("type") != "mousemove":
            return
        now = time.monotonic()
        if now - self._hover_check_last < self._HOVER_THROTTLE_S:
            return
        self._hover_check_last = now
        coords = kwargs.get("coordinates")
        if not coords:
            return
        # Leaflet gives ``[lat, lng]``; shapely uses ``(x=lng, y=lat)``.
        x, y = coords[1], coords[0]
        point = Point(x, y)
        for minx, miny, maxx, maxy, geom, name in self._hover_bbox_cache:
            if minx <= x <= maxx and miny <= y <= maxy and geom.contains(point):
                if self.html.children != [name]:
                    self.html.children = [name]
                return
        if self.html.children:
            self.html.children = []

    def reset(self, change):
        """Reset the map view (remove all the layers)."""
        self.center = [0, 0]
        self.zoom = 3
        self.remove_all()
