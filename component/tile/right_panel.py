from sepal_ui.scripts.gee_interface import GEEInterface
from sepal_ui.solara.components.admin import AdminButton

from component.model.recipe import Recipe
from component.tile.dashboard_components import (
    DashboardDialog,
    DownloadComponent,
    DashboardComputeComponent,
    CompareComponent,
    MapComputeComponent,
    MapDownloadComponent,
)
from component.widget.alert_state import Alert, AlertDialog


def get_right_panel_content(
    gee_interface: GEEInterface,
    recipe: Recipe,
    sepal_session,
    map_,
    theme_toggle=None,
    no_admin=False,
):

    dashboard_dialog = DashboardDialog(theme_toggle=theme_toggle, recipe=recipe)

    shared_alert = Alert()
    AlertDialog.element(w_alert=shared_alert)

    download_component = DownloadComponent(
        gee_interface=gee_interface, recipe=recipe, alert=shared_alert
    )

    dashboard_compute_component = DashboardComputeComponent(
        gee_interface=gee_interface,
        recipe=recipe,
        alert=shared_alert,
        dashboard_dialog=dashboard_dialog,
    )

    compare_component = CompareComponent(
        gee_interface=gee_interface,
        recipe=recipe,
        alert=shared_alert,
        sepal_session=sepal_session,
        map_=map_,
        dashboard_dialog=dashboard_dialog,
    )

    map_compute_component = MapComputeComponent(
        recipe=recipe, map_=map_, gee_interface=gee_interface, alert=shared_alert
    )

    map_download_component = MapDownloadComponent(recipe=recipe, alert=shared_alert)

    # Right panel configuration
    config = {
        "title": "Compute results",
        "icon": "mdi-chart-line",
        "width": 400,
        "description": "Analysis tools for restoration planning results. Generate dashboards, export data, and compare scenarios.",
        "toggle_icon": "mdi-chevron-left",
    }

    # Add dashboard components
    content_data = [
        {"content": [AdminButton(models=recipe.models) if not no_admin else None]},
        {
            "title": "Compute Restoration Map",
            "icon": "mdi-map-marker",
            "content": [map_compute_component],
            "divider": True,
            "description": "Generate the restoration suitability map based on the benefits, constraints and costs layers and configuration.",
        },
        {
            "title": "Export Results",
            "icon": "mdi-download",
            "content": [map_download_component, download_component],
            "divider": True,
            "description": "Export layers and download results as CSV files for external processing.",
        },
        {
            "title": "Dashboard Generation",
            "icon": "mdi-chart-line",
            "content": [dashboard_compute_component, dashboard_dialog],
            "divider": True,
            "description": "Generate detailed dashboard analysis with charts and visualizations.",
        },
        {
            "title": "Compare Scenarios",
            "icon": "mdi-compare",
            "content": [compare_component],
            "description": "Compare results from different restoration scenarios side by side.",
        },
    ]

    return config, content_data
