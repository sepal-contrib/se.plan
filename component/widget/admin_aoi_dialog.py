"""Dialog to add a sub-AOI by picking an admin unit inside the primary AOI.

Admin hierarchy guarantees structural containment, so the GEE containment
check used by drawn / imported geometries can be skipped for this path.
The only round-trip is one ``getInfo`` to materialize the picked admin
unit's geometry as GeoJSON for the ipyleaflet GeoJSON layer.
"""

import logging

import pygaul
import sepal_ui.sepalwidgets as sw
from sepal_ui.aoi.aoi_view import AdminField
from sepal_ui.scripts.gee_interface import GEEInterface

from component.frontend.icons import icon
from component.scripts.aoi_geometry import simplify_fc
from component.widget.base_dialog import BaseDialog
from component.widget.buttons import TextBtn

logger = logging.getLogger("SEPLAN")


def _admin_level(method: str) -> int:
    """Return the integer admin level (0-2) for an ADMIN method, or -1."""
    if not method or not method.startswith("ADMIN"):
        return -1
    try:
        return int(method[5:])
    except (ValueError, IndexError):
        return -1


def _is_admin_eligible(method: str) -> bool:
    """Whether a primary AOI with ``method`` allows an admin sub-area pick."""
    level = _admin_level(method)
    return 0 <= level <= 1  # ADMIN0/ADMIN1 → ADMIN1/ADMIN2 child available


class AdminAoiDialog(BaseDialog):
    """Pick an admin unit one level below the primary AOI as a sub-AOI."""

    def __init__(
        self,
        custom_aoi_dialog,
        gee_interface: GEEInterface,
        map_,
    ):
        super().__init__()
        self.attributes = {"id": "admin_aoi_dialog"}

        self.custom_aoi_dialog = custom_aoi_dialog
        self.gee_interface = gee_interface
        self.map_ = map_

        # Selectors built on each ``open_dialog`` so they reflect the
        # current primary AOI / available child levels. ``_cascade_fields``
        # holds one ``AdminField`` per intermediate level — for a target
        # level deeper than ``parent_level + 1`` the user picks each level
        # in turn (e.g. Departamento, then Municipio).
        self.w_level: "sw.Select | None" = None
        self._cascade_fields: list = []
        self._primary_admin: str = ""
        self._parent_level: int = -1
        self._admin_task = None
        # Caller-supplied dialog to re-open if the user cancels out of this
        # one — used to restore the consolidated Custom Geometries picker
        # after a back-out.
        self._return_to = None

        title = sw.CardTitle(children=["Add admin sub-area"])
        self.header = sw.Html(
            tag="p",
            class_="ma-2",
            children=[""],
        )
        self.body_card = sw.CardText(children=[self.header])
        self.alert = sw.Alert()

        self.btn = TextBtn("Add", gliph=icon("plus"))
        btn_cancel = TextBtn("Cancel", outlined=True)
        action = sw.CardActions(
            children=[sw.Spacer(), btn_cancel, self.btn],
        )
        card = sw.Card(
            class_="ma-0",
            children=[title, self.body_card, self.alert, action],
        )
        self.children = [card]

        btn_cancel.on_event("click", lambda *_: self._cancel())
        self.btn.on_event("click", self.on_submit)

    def _cancel(self, *_):
        """Close the dialog and re-open the caller dialog if any."""
        return_to = self._return_to
        self._return_to = None
        self.close_dialog()
        if return_to is not None:
            return_to.open_dialog()

    def open_dialog(self, *_, return_to=None):
        """(Re)build the level + admin selectors and show the dialog.

        Args:
            return_to: Optional dialog to re-open if the user cancels — used
                to preserve a back-navigation breadcrumb from the
                consolidated Custom Geometries picker.
        """
        if return_to is not None:
            self._return_to = return_to
        primary = self.map_.aoi_model.aoi_model
        method = getattr(primary, "method", "") or ""
        primary_admin = getattr(primary, "admin", "") or ""
        primary_name = (getattr(primary, "name", "") or "").replace("_", " ")

        self.alert.reset()
        self.btn.disabled = False
        self.btn.loading = False
        self._primary_admin = primary_admin

        if not _is_admin_eligible(method):
            self._show_message(
                "The primary AOI is not an administrative area, so admin "
                "sub-units are unavailable. Pick a country or first-level "
                "admin as your primary AOI to use this option."
            )
            super().open_dialog()
            return

        # Level options: every admin level strictly deeper than the primary.
        parent_level = _admin_level(method)
        self._parent_level = parent_level
        available_levels = [lvl for lvl in (1, 2) if lvl > parent_level]
        logger.info(
            "Admin sub-area open: method=%s parent_level=%s available_levels=%s",
            method,
            parent_level,
            available_levels,
        )

        # Use string values to avoid Vuetify's strict-equality oddities when
        # comparing the v-model against item values of mixed numeric types.
        self.w_level = sw.Select(
            v_model=str(available_levels[0]),
            items=[
                {"text": f"Admin level {lvl}", "value": str(lvl)}
                for lvl in available_levels
            ],
            label="Sub-area level",
            class_="mb-2",
            clearable=False,
        )
        self.w_level.observe(self._on_level_change, "v_model")

        try:
            self._cascade_fields = self._build_cascade(available_levels[0])
        except Exception as exc:
            logger.exception("Failed to build admin sub-area selector")
            self._show_message(f"Could not load admin sub-units: {exc}")
            super().open_dialog()
            return

        self.header.children = [
            f"Pick an administrative sub-area inside "
            f"{primary_name or 'your primary AOI'}:"
        ]
        self.body_card.children = [
            self.header,
            self.w_level,
            *self._cascade_fields,
        ]

        super().open_dialog()

    def _build_cascade(self, target_level: int) -> list:
        """Build the chain of ``AdminField`` widgets up to ``target_level``.

        - First field (``parent_level + 1``) is filtered by the primary AOI's
          admin code.
        - Subsequent fields use pysepal's ``AdminField`` parent observer,
          which auto-refreshes the children when the parent's ``v_model``
          changes — so picking a Departamento populates the Municipio
          selector with that Departamento's children, etc.
        """
        fields: list = []
        for lvl in range(self._parent_level + 1, target_level + 1):
            if not fields:
                field = AdminField(level=lvl, gee=True)
                field.get_items(filter_=self._primary_admin)
            else:
                field = AdminField(level=lvl, parent=fields[-1], gee=True)
            fields.append(field)
        return fields

    def _on_level_change(self, change: dict):
        """Rebuild the cascade when the target child level changes."""
        raw = change.get("new")
        if raw is None or self.w_level is None:
            return
        try:
            new_level = int(raw)
        except (TypeError, ValueError):
            return
        try:
            self._cascade_fields = self._build_cascade(new_level)
        except Exception as exc:
            logger.exception("Failed to rebuild admin sub-area selector")
            self.alert.add_msg(
                f"Could not load admin level {new_level} units: {exc}",
                type_="error",
            )
            return
        self.body_card.children = [
            self.header,
            self.w_level,
            *self._cascade_fields,
        ]

    def on_submit(self, *_):
        """Resolve the picked admin unit and forward to ``CustomAoiDialog``.

        For a multi-level cascade (e.g. ADMIN0 → level 2) every field along
        the chain must have a value: the user has to pick the level 1 unit
        before the level 2 dropdown is populated. We surface a clear error
        if any field is left empty so the user knows what to fill in.
        """
        if not self._cascade_fields:
            self.alert.add_msg("Please pick an admin unit.", type_="error")
            return

        for idx, field in enumerate(self._cascade_fields):
            if not field.v_model:
                level = self._parent_level + 1 + idx
                self.alert.add_msg(
                    f"Please pick an admin level {level} unit before " "submitting.",
                    type_="error",
                )
                return

        final = self._cascade_fields[-1]
        admin_code = final.v_model
        admin_text = next(
            (
                item.get("text", admin_code)
                for item in (final.items or [])
                if item.get("value") == admin_code
            ),
            admin_code,
        )

        self.btn.disabled = True
        self.btn.loading = True
        self.alert.reset()

        self._admin_code = admin_code
        self._admin_text = admin_text
        self._admin_task = self.gee_interface.create_task(
            func=self._resolve_admin_async,
            key="admin_subaoi_resolve",
            on_done=self._on_resolved,
            on_error=self._on_resolve_error,
        )
        self._admin_task.start()

    async def _resolve_admin_async(self):
        """Materialize the picked admin unit as a GeoJSON FeatureCollection.

        Returns the GeoJSON dict ready to feed into
        ``CustomAoiDialog.on_new_geom``. We use ``get_info_async`` so the
        resolution doesn't block the kernel — pygaul is lazy and only the
        ``getInfo`` round-trip is slow.
        """
        fc = pygaul.AdmItems(admin=self._admin_code)
        # Simplify server-side: a dense admin unit (e.g. a country with millions
        # of vertices) would otherwise be pulled in full and OOM the kernel. The
        # full-resolution geometry stays server-side for analysis.
        return await self.gee_interface.get_info_async(simplify_fc(fc))

    def _on_resolved(self, geo_json: dict):
        """Forward the materialized geometry to ``CustomAoiDialog``."""
        self.btn.disabled = False
        self.btn.loading = False
        if not geo_json or not geo_json.get("features"):
            self.alert.add_msg(
                "The selected admin unit returned no geometry. "
                "Try a different unit.",
                type_="error",
            )
            return

        # Hand off to the existing rename + commit dialog. The skip flag tells
        # CustomAoiDialog not to run the GEE containment check — admin
        # hierarchy gives us structural containment for free.
        self.close_dialog()
        self.custom_aoi_dialog.on_new_geom(
            feature_collection=geo_json,
            name=self._admin_text or self._admin_code,
            skip_containment_check=True,
            # rebuild the EXACT geometry from the admin code for analysis + tiles
            # (geo_json above is simplified for display only)
            source={"type": "admin", "code": self._admin_code},
        )

    def _on_resolve_error(self, exc: Exception):
        self.btn.disabled = False
        self.btn.loading = False
        logger.exception("Admin sub-area resolution failed", exc_info=exc)
        self.alert.add_msg(
            f"Could not load the selected admin unit: {exc}",
            type_="error",
        )

    def _show_message(self, text: str):
        """Render a plain message in place of the selector."""
        self.body_card.children = [sw.Html(tag="p", class_="ma-2", children=[text])]
