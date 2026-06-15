"""Right-panel header showing the current recipe name and a Save button.

Renders compact: "<recipe-name> • saved/unsaved" with a save icon button to
the right. Observes ``recipe.recipe_session_path`` and ``recipe.new_changes``
so the label and dirty state stay in sync without manual wiring from
callers.
"""

from pathlib import Path

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component.frontend.icons import icon
from component.message import cm
from component.model.recipe import Recipe
from component.widget.alert_state import Alert
from component.widget.buttons import IconBtn
from component.widget.custom_widgets import RecipeInspector


class RecipeHeader(sw.Layout):
    """Pinned header: recipe name + saved/unsaved indicator + Save button."""

    def __init__(self, recipe: Recipe, alert: Alert, **kwargs):
        self.class_ = "d-flex align-center pa-2"
        self.attributes = {"id": "recipe_header"}
        super().__init__(**kwargs)

        self.recipe = recipe
        self.alert = alert

        self.name_field = sw.TextField(
            v_model=self._format_name(),
            dense=True,
            hint=self._format_status(),
            persistent_hint=True,
            class_="mr-2 flex-grow-1",
        )
        self.btn_view = IconBtn(gliph="mdi-eye")
        self.btn_view.attributes = {"id": "btn_recipe_header_view"}
        self.btn_save = IconBtn(gliph=icon("save"))
        self.btn_save.attributes = {"id": "btn_recipe_header_save"}

        self.inspector = RecipeInspector()

        self.children = [
            self.name_field,
            self.btn_save,
            self.btn_view,
            self.inspector,
        ]

        self.recipe.observe(self._on_path_change, "recipe_session_path")
        self.recipe.observe(self._on_changes, "new_changes")
        self.btn_view.on_event("click", self._on_view)
        self.btn_save.on_event("click", self._on_save)
        self.name_field.on_event("blur", self._commit_name)
        self.name_field.on_event("keydown.enter", self._commit_name)

    def _format_name(self) -> str:
        if not self.recipe.recipe_session_path:
            return "No recipe"
        return Path(self.recipe.recipe_session_path).stem

    def _format_status(self) -> str:
        if not self.recipe.recipe_session_path:
            return ""
        return "unsaved" if self.recipe.new_changes else "saved"

    def _on_path_change(self, _):
        self.name_field.v_model = self._format_name()
        self.name_field.hint = self._format_status()

    def _on_changes(self, _):
        self.name_field.hint = self._format_status()

    def _commit_name(self, widget, event, data):
        """Normalize the typed name and rewrite ``recipe_session_path``.

        Only changes the in-memory path; the file isn't created/renamed
        until the user clicks Save. Empty/unchanged input is ignored and
        the field is restored to the canonical name.
        """
        new_name = (widget.v_model or "").strip()
        if new_name:
            new_name = su.normalize_str(new_name)
        current = self._format_name()
        if new_name and new_name != current:
            self.recipe.recipe_session_path = self.recipe.get_recipe_path(new_name)
        else:
            self.name_field.v_model = current

    def _on_view(self, *_):
        name = self._format_name()
        self.inspector.set_data(self.recipe.to_dict(), recipe_name=name)

    def _on_save(self, *_):
        path = self.recipe.recipe_session_path
        if not path:
            self.alert.add_msg(cm.recipe.error.no_name, type_="warning")
            return
        try:
            self.recipe.save(path)
            self.alert.add_msg(
                cm.recipe.states.save.format(path), type_="success"
            )
        except Exception as exc:
            self.alert.add_msg(str(exc), type_="error")
