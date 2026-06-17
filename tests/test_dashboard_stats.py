"""Regression test: dashboard area stats must not dissolve a dense AOI.

The per-AOI dashboard statistics reduced over ``geometry=aoi`` (the primary
feature collection), which dissolves the whole AOI and exceeds EE's 2M-edge
limit for dense GAUL 2024 boundaries (e.g. Indonesia, ~2.4M edges). The fix
clips the image to the AOI and reduces over its bounding box instead.
"""

import ee
import pygaul

from component.scripts import statistics


def test_get_image_stats_handles_dense_aoi(monkeypatch):
    """Suitability-area stats over Indonesia must evaluate without dissolving."""
    # The dissolve fails regardless of scale; coarsening the fixed stats scale
    # only speeds up the post-fix reduction so the test stays fast.
    monkeypatch.setattr(statistics, "STATS_SCALE_M", 10000)

    aoi = pygaul.AdmItems(name="Indonesia")
    result = statistics.get_image_stats(ee.Image(3), ee.Image(1), aoi).getInfo()

    assert result["total"] is not None
