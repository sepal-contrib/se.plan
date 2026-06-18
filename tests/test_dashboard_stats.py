"""Regression: dashboard area stats must not dissolve a dense AOI."""

import ee
import pygaul

from component.scripts import statistics


def test_get_image_stats_handles_dense_aoi(monkeypatch):
    """Suitability-area stats over Indonesia must evaluate without dissolving."""
    # coarsen the fixed scale so the post-fix reduction stays fast
    monkeypatch.setattr(statistics, "STATS_SCALE_M", 10000)

    aoi = pygaul.AdmItems(name="Indonesia")
    result = statistics.get_image_stats(ee.Image(3), ee.Image(1), aoi).getInfo()

    assert result["total"] is not None
