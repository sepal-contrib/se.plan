import csv
import io
import logging
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import component.parameter.gui_params as param
from component.message import cm
from component.parameter.directory import result_dir
from component.parameter.file_params import layer_list
from component.scripts.statistics import STATS_SCALE_M
from component.types import RecipeStatsDict

from sepal_ui.solara import get_current_sepal_client

logger = logging.getLogger("SEPLAN")

AGGREGATION_LABEL = {
    "benefit": "mean",
    "constraint": "coverage",
    "cost": "sum",
    "suitability": "area",
}

VALUE_KEY = {
    "benefit": "mean",
    "constraint": "percent",
    "cost": "sum",
}

THEME_DISPLAY = {
    "benefit": "Benefit",
    "constraint": "Constraint",
    "cost": "Cost",
    "suitability": "Suitability",
}

CSV_COLUMNS = [
    "Recipe",
    "Area",
    "AOI type",
    "Theme",
    "Indicator",
    "Unit",
    "Aggregation",
    "Value",
]


def _layer_label(layer_id: str) -> str:
    """Human-readable name for a layer; falls back to a humanized layer_id."""
    entry = cm.layers.get(layer_id) if hasattr(cm.layers, "get") else None
    if entry is not None:
        name = getattr(entry, "name", None) or (entry.get("name") if hasattr(entry, "get") else None)
        if name:
            return name
    return layer_id.replace("_", " ").capitalize()


def _build_unit_lookup() -> dict:
    df = pd.read_csv(layer_list).fillna("")
    return dict(zip(df["layer_id"], df["unit"]))


_UNIT_LOOKUP = _build_unit_lookup()


def _format_value(v) -> str:
    if v is None:
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ""
    if math.isnan(f) or math.isinf(f):
        return ""
    if f != 0 and abs(f) < 0.1:
        return f"{f:.4g}"
    return f"{f:.2f}"


def _humanize_primary_area_name(area_name: str) -> str:
    """`PER_Amazonas` → `PER — Amazonas`. Only applied to the primary AOI."""
    if "_" in area_name:
        first, rest = area_name.split("_", 1)
        return f"{first} — {rest}"
    return area_name


def _build_rows(recipe_name: str, area_stats: dict) -> list:
    unit_for = _UNIT_LOOKUP
    rows = []

    for idx, (area_name, area_data) in enumerate(area_stats.items()):
        is_primary = idx == 0
        aoi_type = "Primary" if is_primary else "Sub-region"
        area_display = (
            _humanize_primary_area_name(area_name) if is_primary else area_name
        )

        for category in ("benefit", "constraint", "cost"):
            details = area_data.get(category) or []
            value_key = VALUE_KEY[category]
            for entry in details:
                for layer_id, content in entry.items():
                    raw_value = content.get("values", {}).get(value_key)
                    # Constraints always report % of AOI covered, not the
                    # underlying raster's native unit.
                    unit = (
                        "% of AOI"
                        if category == "constraint"
                        else unit_for.get(layer_id, "")
                    )
                    rows.append(
                        {
                            "Recipe": recipe_name,
                            "Area": area_display,
                            "AOI type": aoi_type,
                            "Theme": THEME_DISPLAY[category],
                            "Indicator": _layer_label(layer_id),
                            "Unit": unit,
                            "Aggregation": AGGREGATION_LABEL[category],
                            "Value": _format_value(raw_value),
                        }
                    )

        suit = area_data.get("suitability") or {}
        for v in suit.get("values", []):
            rows.append(
                {
                    "Recipe": recipe_name,
                    "Area": area_display,
                    "AOI type": aoi_type,
                    "Theme": THEME_DISPLAY["suitability"],
                    "Indicator": param.SUITABILITY_LEVELS[v["image"]],
                    "Unit": "ha",
                    "Aggregation": AGGREGATION_LABEL["suitability"],
                    "Value": _format_value(v.get("sum")),
                }
            )

        rows.append(
            {
                "Recipe": recipe_name,
                "Area": area_display,
                "AOI type": aoi_type,
                "Theme": THEME_DISPLAY["suitability"],
                "Indicator": "Total",
                "Unit": "ha",
                "Aggregation": AGGREGATION_LABEL["suitability"],
                "Value": _format_value(suit.get("total")),
            }
        )

    return rows


def _build_metadata(recipe_name: str, area_stats: dict) -> list:
    area_keys = list(area_stats.keys())
    primary_name = area_keys[0]
    sub_regions = area_keys[1:]

    lines = [
        f"# Recipe: {recipe_name}",
        f"# Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"# Primary AOI: {primary_name}",
    ]
    if sub_regions:
        lines.append("# Sub-regions: " + ", ".join(sub_regions))
    lines.append(f"# Scale (m): {STATS_SCALE_M}")
    lines.append(f"# Areas: {len(area_keys)}")
    return lines


def export_as_csv(recipe_summary_stats: RecipeStatsDict):
    """Write the dashboard summary statistics to a real CSV file.

    Output layout: a metadata block of `# key: value` comment lines, followed
    by a tabular section with the columns in `CSV_COLUMNS`. Read back with
    `pd.read_csv(path, comment='#')`.
    """
    recipe_name, area_stats = next(iter(recipe_summary_stats.items()))

    sepal_session = get_current_sepal_client()
    if sepal_session:
        csv_folder = sepal_session.get_remote_dir("module_results/se.plan/csv_results")
    else:
        csv_folder = result_dir / "results"
        csv_folder.mkdir(exist_ok=True)

    session_results_path = (csv_folder / recipe_name).with_suffix(".csv")

    metadata_lines = _build_metadata(recipe_name, area_stats)
    rows = _build_rows(recipe_name, area_stats)

    buf = io.StringIO()
    buf.write("\n".join(metadata_lines))
    buf.write("\n")
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    text = buf.getvalue()

    if sepal_session:
        sepal_session.set_file(str(session_results_path), text, overwrite=True)
    else:
        Path(session_results_path).write_text(text, encoding="utf-8")

    return session_results_path
