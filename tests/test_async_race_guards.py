"""Regression: async task completions must be rejected after cancel/supersede.

Admin resolution and custom-geometry containment run as background GEE tasks.
If the user cancels or makes a newer selection while a task is in flight, the
stale completion must NOT commit/forward anything. Each path carries a monotonic
generation token (and, for admin, the per-selection data) in the task result;
the ``on_done``/``on_error`` handlers drop a result whose token no longer matches.

These exercise the sync completion handlers directly (no GEE needed) — the
load-bearing guard, since the completion tail has no further ``await`` for
``cancel()`` to interrupt.
"""

import types

from component.widget.admin_aoi_dialog import AdminAoiDialog
from component.widget.custom_aoi_dialog import CustomAoiDialog


def _admin_stub(gen: int):
    """An AdminAoiDialog with only the fields ``_on_resolved`` touches.

    Deliberately does NOT set ``_admin_code``/``_admin_text`` — if the handler
    regressed to reading those mutable fields (the original bug) it would raise
    AttributeError instead of using the per-result data.
    """
    dlg = AdminAoiDialog.__new__(AdminAoiDialog)
    dlg._admin_gen = gen
    dlg.btn = types.SimpleNamespace(disabled=True, loading=True)
    dlg.alert = types.SimpleNamespace(add_msg=lambda *a, **k: None)
    dlg.close_dialog = lambda *a, **k: None
    calls = []
    dlg.custom_aoi_dialog = types.SimpleNamespace(
        on_new_geom=lambda **kw: calls.append(kw)
    )
    return dlg, calls


def test_admin_on_resolved_rejects_stale_gen():
    """A resolution whose token was superseded must not forward a geometry."""
    dlg, calls = _admin_stub(gen=2)  # current generation is 2
    dlg._on_resolved(
        {"gen": 1, "code": "A", "text": "Area A", "geo_json": {"features": [{}]}}
    )
    assert calls == []  # stale (gen 1 != 2) -> dropped


def test_admin_on_resolved_uses_result_not_mutable_state():
    """A fresh resolution forwards the geometry with source from the RESULT."""
    dlg, calls = _admin_stub(gen=1)
    dlg._on_resolved(
        {"gen": 1, "code": "123", "text": "Java", "geo_json": {"features": [{}]}}
    )
    assert len(calls) == 1
    kw = calls[0]
    assert kw["name"] == "Java"
    assert kw["source"] == {"type": "admin", "code": "123"}
    assert kw["skip_containment_check"] is True


def _validate_stub(gen: int):
    """A CustomAoiDialog with only the fields the validate handlers touch."""
    dlg = CustomAoiDialog.__new__(CustomAoiDialog)
    dlg._validate_gen = gen
    dlg.btn = types.SimpleNamespace(disabled=True, loading=True)
    dlg.alert = types.SimpleNamespace(add_msg=lambda *a, **k: None)
    committed = []
    dlg._commit_save = lambda: committed.append(True)
    return dlg, committed


def test_validate_done_rejects_stale_gen():
    """A verdict from a cancelled/superseded save must not commit."""
    dlg, committed = _validate_stub(gen=2)
    dlg._on_validate_done({"gen": 1, "outside_count": 0})
    assert committed == []  # stale -> no commit


def test_validate_done_commits_when_inside():
    """A fresh verdict with nothing outside commits the sub-AOI."""
    dlg, committed = _validate_stub(gen=1)
    dlg._on_validate_done({"gen": 1, "outside_count": 0})
    assert committed == [True]


def test_validate_done_blocks_when_outside():
    """A fresh verdict with geometry outside the primary AOI does not commit."""
    dlg, committed = _validate_stub(gen=1)
    dlg._on_validate_done({"gen": 1, "outside_count": 2})
    assert committed == []  # surfaced as an error, no commit


def test_validate_error_rejects_stale_gen():
    """A stale validation error must not reset the (reused) dialog UI."""
    dlg, _ = _validate_stub(gen=2)
    dlg.btn.disabled = True
    dlg._on_validate_error(RuntimeError("boom"), gen=1)
    assert dlg.btn.disabled is True  # stale -> handler returned before resetting


def test_validate_error_resets_on_fresh_gen():
    """A current validation error resets the button so the user can retry."""
    dlg, _ = _validate_stub(gen=1)
    dlg.btn.disabled = True
    dlg._on_validate_error(RuntimeError("boom"), gen=1)
    assert dlg.btn.disabled is False
