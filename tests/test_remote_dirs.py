"""Remote writers must create their folder with parents.

pysepal-api >= 0.3 no longer creates ``module_results/se.plan`` when the
SepalClient is built, so a non-recursive createFolder of a subfolder fails
for users who have never saved anything.
"""

from pathlib import PurePosixPath
from types import SimpleNamespace
from unittest.mock import MagicMock

from component.model.recipe import Recipe


def _client(folder: str) -> MagicMock:
    client = MagicMock()
    client.get_remote_dir.return_value = PurePosixPath(folder)
    return client


def test_recipe_path_creates_parents():
    client = _client("module_results/se.plan/recipes")

    path = Recipe.get_recipe_path(SimpleNamespace(sepal_session=client), "my_recipe")

    client.get_remote_dir.assert_called_once_with(
        "module_results/se.plan/recipes", parents=True
    )
    assert path == "module_results/se.plan/recipes/my_recipe.json"


def test_csv_export_creates_parents(monkeypatch):
    from component.scripts import compute

    client = _client("module_results/se.plan/csv_results")
    monkeypatch.setattr(compute, "get_current_sepal_client", lambda: client)
    monkeypatch.setattr(compute, "_build_metadata", lambda *a: ["# x"])
    monkeypatch.setattr(compute, "_build_rows", lambda *a: [])

    compute.export_as_csv({"my_recipe": {}})

    client.get_remote_dir.assert_called_once_with(
        "module_results/se.plan/csv_results", parents=True
    )
    client.set_file.assert_called_once()
