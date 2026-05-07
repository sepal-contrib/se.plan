"""Solara legend overlay for SEPLAN's main map.

Mounts pysepal's body-level ``LegendComponent`` so the suitability legend
sits as a floating overlay aware of MapApp's drawer and right-panel offsets,
replacing the legacy ipyleaflet ``WidgetControl``-based ``SuitabilityLegend``.
"""

from dataclasses import asdict

import solara
from pysepal.solara.components.legend import (
    DiscreteEntry,
    GradientEntry,
    LegendComponent,
    LegendData,
)

from component.message import cm


def suitability_legend() -> LegendData:
    """Canonical legend data for the restoration suitability index."""
    return LegendData(
        gradients=[
            GradientEntry(
                colors=["#edf8fb", "#66c2a4", "#006d2c"],
                labels=[
                    cm.map.legend.class_.vlow,
                    cm.map.legend.class_.low,
                    cm.map.legend.class_.medium,
                    cm.map.legend.class_.high,
                    cm.map.legend.class_.vhigh,
                ],
                title=cm.map.legend.title,
            ),
        ],
        items=[DiscreteEntry(label=cm.map.legend.class_.nodata, color="#353535")],
    )


_HIDE_WHEN_DIALOG_CSS = """
/* pysepal toggles body.sepal-modal-open only for MapApp step dialogs.
   se.plan also opens many ad-hoc ipyvuetify v-dialogs (custom AOI,
   scenarios, import, etc.) — :has() lets us hide the legend while ANY
   Vuetify dialog overlay is mounted in the document. */
body:has(.v-dialog__content--active) .sepal-legend,
body:has(.v-overlay--active) .sepal-legend {
    display: none !important;
}
"""


@solara.component
def SuitabilityLegendOverlay():
    """Floating suitability-index legend over the main map.

    Always rendered, starts collapsed (icon pill). The user expands /
    re-collapses via the pill click; ``LegendComponent`` keeps that toggle
    in its own Vue state, so no Python reactive is needed and the parent
    Page doesn't re-render on toggle.
    """
    solara.Style(_HIDE_WHEN_DIALOG_CSS)
    LegendComponent(
        legend_data=asdict(suitability_legend()),
        visible=True,
        collapsed=True,
    )
