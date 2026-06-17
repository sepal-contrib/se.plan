import logging

from sepal_ui import mapping as sm
from sepal_ui.aoi.aoi_view import AoiView
from sepal_ui.message import ms

from component.model.aoi_model import SeplanAoi

logger = logging.getLogger("SEPLAN")


class SeplanAoiView(AoiView):
    def __init__(self, model: SeplanAoi, app_model=None, **kwargs: dict):
        # ``self.model`` will be the inner ``AoiModel`` after super().__init__,
        # so stash the SeplanAoi wrapper for callbacks that need the
        # LMIC traits (which live on the wrapper, not the inner model).
        self.seplan_aoi = model
        kwargs.update(
            {
                "methods": ["-POINTS"],
                "class_": "d-block pa-2 py-4",
                "model": model.aoi_model,
                "elevation": 0,
            }
        )

        super().__init__(**kwargs)

        # Stash app_model so the DRAW handler can close the MapApp dialog
        # (``app_model.step_open = False`` propagates to ``MapApp.step_open``
        # via the model binding, which the Vue watcher uses to close the
        # active step dialog).
        self._app_model = app_model

        # Close the AOI dialog the moment the user picks DRAW so the map is
        # uncovered for drawing. The submit step is auto-fired by the draw
        # event handler below, so the user never needs to reopen the dialog.
        if self.w_method is not None:
            self.w_method.observe(self._maybe_close_dialog, "v_model")

        # Reset the method dropdown every time a step dialog opens. Without
        # this, picking DRAW once leaves ``w_method.v_model = "DRAW"`` after
        # the auto-close; reopening the AOI dialog still shows DRAW, so the
        # ``v_model`` observer doesn't fire again on a second pick. Resetting
        # to ``None`` on each open guarantees the next pick is always a real
        # change.
        if app_model is not None:
            app_model.observe(self._reset_method_on_open, "step_open")

        # AoiView hardcodes the legacy ``sm.DrawControl`` for the DRAW method
        # (pysepal/aoi/aoi_view.py:349). Swap it to Geoman so both draw flows
        # (primary AOI here, sub-AOIs on SeplanMap.dc) use the same toolbar.
        if self.map_ is not None and hasattr(sm, "GeomanDrawControl"):
            if not isinstance(self.aoi_dc, sm.GeomanDrawControl):
                if self.aoi_dc is not None:
                    self.aoi_dc.hide()
                self.aoi_dc = sm.GeomanDrawControl(self.map_)
                self.aoi_dc.hide()
            # Defensive: mirror Geoman create/remove events into ``self.data``.
            # The JS view should sync via ``layers_to_data`` + ``save_changes``,
            # but if the round-trip misfires, ``aoi_dc.to_json()`` would return
            # an empty FeatureCollection and the AOI would silently stay empty.
            self.aoi_dc.on_draw(self._mirror_draw_event)

        self.btn.small = True

        model.observe(self.update_view, "set_map")
        model.observe(self.reset_view, "reset_view")

        # Close the AOI step dialog automatically once the primary AOI is
        # set AND the LMIC verdict is in. DRAW closes eagerly on method
        # pick (see ``_maybe_close_dialog``); for ADMIN/ASSET/SHAPE we wait
        # for the LMIC checker (custom_aoi_tile.AoiView) to bump
        # ``aoi_lmic_checked``. If the AOI is outside LMIC, the dialog
        # stays open so the user can read the warning before retrying.
        model.observe(self._close_on_aoi_set, "aoi_lmic_checked")

    def _close_on_aoi_set(self, change):
        if not change.get("new") or self._app_model is None:
            return
        if not getattr(self.seplan_aoi, "aoi_lmic_valid", True):
            return
        # Partial-coverage / unverifiable AOIs are usable but carry a warning;
        # keep the dialog open so the user actually reads it before continuing.
        if getattr(self.seplan_aoi, "aoi_lmic_warning", False):
            return
        self._app_model.step_open = False

    def _mirror_draw_event(self, target, action, geo_json):
        """Append created features into ``aoi_dc.data`` and schedule submit.

        Geoman delivers ``geo_json`` as a list. We dedupe by geometry so the
        explicit append stays idempotent against the JS-side ``layers_to_data``
        sync. The submit step runs on the GEE event loop via
        ``gee_interface.create_task`` so the Solara kernel thread stays
        responsive while the polygon is converted into an AOI map layer.
        """
        if action != "create":
            return
        new_feats = geo_json if isinstance(geo_json, list) else [geo_json]
        existing_geoms = [f.get("geometry") for f in self.aoi_dc.data]
        appended = list(self.aoi_dc.data)
        for feat in new_feats:
            if feat.get("geometry") not in existing_geoms:
                appended.append(feat)
        if len(appended) != len(self.aoi_dc.data):
            self.aoi_dc.data = appended

        self._schedule_auto_submit()

    def _schedule_auto_submit(self):
        """Run the AOI submit on a GEE-loop background task (non-blocking).

        Falls back to firing the validation button synchronously when no
        ``gee_interface`` is available (e.g. ``gee=False`` testing path).
        """
        gee_interface = getattr(self.model, "gee_interface", None)
        if not self.gee or gee_interface is None:
            self.btn.fire_event("click", None)
            return

        task = gee_interface.create_task(
            func=self._auto_submit_async,
            key="aoi_auto_submit",
            on_error=self._on_auto_submit_error,
        )
        # Hold a reference so the task isn't garbage-collected before it runs.
        self._auto_submit_task = task
        task.start()

    async def _auto_submit_async(self):
        """Async equivalent of pysepal's ``_update_aoi`` for the DRAW path.

        Mirrors the work done by clicking the validation button, but uses
        ``get_info_async`` / ``add_ee_layer_async`` so the GEE round-trips
        don't block the kernel thread.
        """
        if self.aoi_dc is None:
            return

        self.model.geo_json = self.aoi_dc.to_json()
        self.model.set_object()  # builds in-memory ee.FeatureCollection

        if self.map_ is None:
            self.updated += 1
            return

        fc = self.model.feature_collection
        if fc is None:
            return

        # Bounds → zoom. Per-feature bounding boxes avoid Collection.geometry's
        # 2M-edge limit on large AOIs (see AoiModel.total_bounds_async).
        bounds = await self.model.total_bounds_async()

        self.map_.remove_layer("aoi", none_ok=True)
        self.map_.zoom_bounds(bounds)

        # add_ee_layer_async resolves the slow getMapId off the kernel thread.
        await self.map_.add_ee_layer_async(fc, {}, "aoi")

        self.aoi_dc.hide()
        self.alert.add_msg(ms.aoi_sel.complete, "success")
        self.updated += 1

    def _on_auto_submit_error(self, exc: Exception):
        """Surface auto-submit failures via the AoiView alert area.

        Also reopens the AOI step dialog: ``_maybe_close_dialog`` closes it
        eagerly when the user picks DRAW so the map is uncovered, but if the
        async submit fails (e.g. Geoman/JS sync race produced an empty
        FeatureCollection) the user would otherwise be stranded with no
        visible way back to the AOI selector.
        """
        logger.exception("AOI auto-submit failed", exc_info=exc)
        self.alert.add_msg(str(exc), type_="error")
        if self._app_model is not None:
            self._app_model.step_open = True

    def _update_aoi(self, *args):
        """Async-zoom submit for ADMIN/ASSET/SHAPE (DRAW uses ``_auto_submit_async``).

        The build stays synchronous — identical to pysepal's ``_update_aoi`` —
        so recipe-import timing and the wrapper's ``_loading`` guard (which
        protects restored sub-AOIs) are unchanged. Only the EE-heavy extent +
        zoom is deferred to the GEE loop, and it uses the async per-feature
        ``total_bounds_async`` so dense GAUL 2024 boundaries (e.g. Indonesia,
        ~2.4M edges) don't blow ``Collection.geometry``'s 2M-edge limit — which
        is exactly what pysepal's sync ``total_bounds`` dissolve hit.
        """
        gee_interface = getattr(self.model, "gee_interface", None)
        if not self.gee or gee_interface is None or self.map_ is None:
            # non-gee / headless: keep pysepal's synchronous behaviour
            return super()._update_aoi(*args)

        self.model.set_object()
        self.alert.add_msg(ms.aoi_sel.complete, "success")
        if self.model.feature_collection is None:
            return self

        task = gee_interface.create_task(
            func=self._zoom_async,
            key="aoi_zoom",
            on_error=self._on_auto_submit_error,
        )
        self._zoom_task = task  # hold a ref so the task isn't GC'd
        task.start()
        return self

    async def _zoom_async(self):
        """Zoom to the AOI extent and add its layer — off the kernel thread.

        Uses ``total_bounds_async`` (per-feature bounding boxes) so the zoom box
        for large countries never requires dissolving the whole collection.
        """
        bounds = await self.model.total_bounds_async()
        self.map_.remove_layer("aoi", none_ok=True)
        self.map_.zoom_bounds(bounds)

        await self.map_.add_ee_layer_async(self.model.feature_collection, {}, "aoi")

        if self.aoi_dc is not None:
            self.aoi_dc.hide()
        self.updated += 1

    def update_view(self, *args):
        """Update the view when the feature collection is updated."""
        self.btn.fire_event("click", None)

    def reset_view(self, *args):
        """Reset the view when the feature collection is updated."""
        # I have to do this wrapper to avoid changing the sepal_ui model which
        # not receives any extra argument
        self.reset()

    def _maybe_close_dialog(self, change):
        """Close the AOI step dialog when the user picks DRAW.

        ``app_model.step_open`` is bidirectionally linked to ``MapApp.step_open``,
        so flipping it here triggers the Vue watcher in MapApp that closes the
        active step dialog. The user can re-open the AOI drawer button to come
        back if they want to change the method.
        """
        if change.get("new") == "DRAW" and self._app_model is not None:
            self._app_model.step_open = False

    def _reset_method_on_open(self, change):
        """Clear the method dropdown when the user is starting a fresh AOI.

        ``step_open`` toggles True for every dialog activation. Resetting
        ``w_method.v_model`` is what enables the DRAW auto-close to fire
        again on a second pick (the v_model observer needs an actual change
        to trigger). However, the parent ``AoiView._activate`` reacts to
        ``v_model -> None`` by also setting ``w_draw.v_model = None``, which
        is bound to ``model.name`` — so a blind reset wipes the just-saved
        AOI name and the recipe exports as ``N/A``. Gate on ``model.name``:
        reset only when nothing has been validated yet.
        """
        # ``self.model`` is the ``SeplanAoi`` wrapper (no ``name`` trait);
        # the actual AOI name lives on the inner ``aoi_model``. Reach
        # through the wrapper so the gate isn't a no-op.
        inner = getattr(self.seplan_aoi, "aoi_model", None)
        if (
            change.get("new")
            and self.w_method is not None
            and not getattr(inner, "name", None)
        ):
            self.w_method.v_model = None
