"""
Individual dashboard components for the right panel stacking system.
These replace the monolithic DashboardTile approach.
"""

import logging
import asyncio

from component.tile.dashboard_tile import OverallDashboard, ThemeDashboard
from component.widget.custom_widgets import MapInfoDialog
import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts.gee_interface import GEEInterface

from component import parameter as cp
from component import widget as cw
from component.message import cm
from component.model.recipe import Recipe
from component.scripts.compute import export_as_csv
from component.scripts.statistics import get_summary_statistics_async
from component.widget.alert_state import Alert
from component.widget.base_dialog import BaseDialog, MapDialog
from component.widget.buttons import IconBtn, TextBtn
from component.scripts.gee import create_layer

logger = logging.getLogger("SEPLAN")


class MapComputeComponent(sw.Layout):
    """Component for map computation functionality"""

    def __init__(
        self, recipe: Recipe, map_, gee_interface: GEEInterface, alert: Alert, **kwargs
    ):
        super().__init__(**kwargs)
        self.recipe = recipe
        self.map_ = map_
        self.gee_interface = gee_interface
        self.alert = alert

        self.btn_compute = sw.TaskButton(cm.compute.btn, small=True, block=True)
        self.btn_info = IconBtn(gliph="fa-solid fa-circle-info")
        self.info_dialog = MapInfoDialog()
        self.title = sw.CardTitle(
            children=[
                "Compute Restoration Map",
                sw.Spacer(),
                self.btn_info,
            ]
        )

        self.children = [
            self.info_dialog,
            self.btn_compute,
        ]

        self.btn_info.on_event("click", lambda *_: self.info_dialog.open_dialog())

        # Configure the compute button with the task
        self._configure_compute_task()

    def _configure_compute_task(self):
        """Configure the TaskButton instance with the task factory for computing all maps."""

        def create_compute_maps_task():
            def callback(result):
                task = self.btn_compute._task
                if task:
                    bounds, map_id_dicts = task.result
                    logger.debug(
                        f"All maps computed. Results: {len(map_id_dicts) if map_id_dicts else 0} maps"
                    )

                    self.map_.zoom_bounds((*bounds[0], *bounds[2]))

                    if map_id_dicts:
                        layer_names = [
                            cm.layer.index.benefit_index.name,
                            cm.layer.index.benefit_cost_index.name,
                            cm.layer.index.constraint_index.name,
                        ]

                        for i, map_id_dict in enumerate(map_id_dicts):
                            if isinstance(map_id_dict, Exception):
                                logger.error(f"Error in task {i}: {map_id_dict}")
                                self.alert.add_msg(
                                    f"Failed to load {layer_names[i]}: {map_id_dict}",
                                    type_="error",
                                )
                                continue

                            logger.debug(f"Adding layer {i}: {layer_names[i]}")
                            self.map_.add_layer(
                                create_layer(map_id_dict, layer_names[i])
                            )

            return self.gee_interface.create_task(
                func=self._get_maps,
                key="compute_all_maps",
                on_done=callback,
                on_error=lambda e: self.alert.add_msg(str(e), type_="error"),
            )

        self.btn_compute.configure(task_factory=create_compute_maps_task)

    async def _get_maps(self):
        """Compute the restoration maps."""

        self.map_.clean_map()

        aoi = self.recipe.seplan_aoi.feature_collection

        benefit_index = self.recipe.seplan.get_benefit_index(clip=True)
        benefit_cost_index = (
            self.recipe.seplan.get_benefit_cost_index(clip=True).multiply(4).add(1)
        )
        constraint_index = self.recipe.seplan.get_constraint_index().unmask(0).clip(aoi)

        tasks = [
            self.gee_interface.get_info_async(aoi.bounds().coordinates().get(0)),
            self.gee_interface.get_map_id_async(benefit_index, cp.layer_vis),
            self.gee_interface.get_map_id_async(benefit_cost_index, cp.layer_vis),
            self.gee_interface.get_map_id_async(constraint_index, cp.layer_vis),
        ]

        bounds, benef_idx_id, cost_idx_id, const_id = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        return bounds, (benef_idx_id, cost_idx_id, const_id)


class MapDownloadComponent(sw.Layout):
    """Component for map download functionality"""

    def __init__(self, recipe: Recipe, alert: Alert, **kwargs):
        super().__init__(**kwargs)
        self.recipe = recipe
        self.alert = alert

        self.btn_download = TextBtn("Export Map", block=True)

        # Create download dialog
        self.download_map_dialog = cw.ExportMapDialog(self.recipe, alert=self.alert)

        self.btn_download.on_event(
            "click", lambda *_: self.download_map_dialog.open_dialog()
        )
        self.children = [
            self.btn_download,
            self.download_map_dialog,
        ]


class DashboardDialog(MapDialog):
    """Dialog to display the dashboard results"""

    def __init__(self, recipe, theme_toggle, **kwargs):
        super().__init__(persistent=False, **kwargs)
        self.max_width = "90vw"
        self.height = "80vh"
        self.recipe = recipe

        self.overall_dash = OverallDashboard(theme_toggle=theme_toggle)
        self.theme_dash = ThemeDashboard(theme_toggle=theme_toggle)

        # Create content layout - stacked vertically
        content_layout = sw.Layout(
            children=[self.overall_dash, self.theme_dash],
            class_="pa-4 d-flex flex-column",
        )

        # Create close button
        close_btn = sw.Btn("Close", outlined=True, class_="ma-2")
        close_btn.on_event("click", self.close_dialog)

        # Create dialog content
        self.children = [
            sw.Card(
                children=[
                    sw.CardTitle(children=["Dashboard Results"]),
                    sw.CardText(children=[content_layout]),
                    sw.CardActions(children=[sw.Spacer(), close_btn]),
                ]
            )
        ]

    def set_results(self, summary_stats, recipes=None):
        """Set the results for the dashboard"""
        logger.debug(f"Setting results in DashboardDialog: {summary_stats}")

        if not recipes:
            # Set summary for both dashboards
            self.overall_dash.set_summary([summary_stats])
            self.theme_dash.set_summary([self.recipe], [summary_stats])

        else:
            self.overall_dash.set_summary(summary_stats)
            self.theme_dash.set_summary(recipes, summary_stats)

        logger.debug("Opening dialog")
        self.open_dialog()


class DownloadComponent(sw.Layout):
    """Component for CSV export functionality"""

    def __init__(
        self, gee_interface: GEEInterface, recipe: Recipe, alert: Alert, **kwargs
    ):
        super().__init__(**kwargs)
        self.gee_interface = gee_interface
        self.recipe = recipe
        self.alert = alert
        self.summary_stats = None

        self.btn_download = sw.TaskButton(
            cm.dashboard.toolbar.btn.download.title, small=True, block=True
        )

        self.children = [self.btn_download]

        self._configure_csv_export()

    def _configure_csv_export(self):
        """Configure the CSV export functionality"""

        def create_csv_task():
            def callback(*_):
                task = self.btn_download._task
                if task:
                    self.summary_stats = task.result
                    session_results_path = export_as_csv(self.summary_stats)
                    self.alert.add_msg(
                        f"File successfully saved in {session_results_path}", "success"
                    )

            return self.gee_interface.create_task(
                func=get_summary_statistics_async,
                key="create_csv_task",
                on_done=callback,
                on_error=lambda e: self.alert.add_msg(str(e), type_="error"),
            )

        self.btn_download.configure(
            task_factory=create_csv_task,
            start_args=(self.gee_interface, self.recipe),
        )


class DashboardComputeComponent(sw.Layout):
    """Component for dashboard computation and viewing"""

    def __init__(
        self,
        gee_interface: GEEInterface,
        recipe: Recipe,
        alert: Alert,
        dashboard_dialog: DashboardDialog,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.gee_interface = gee_interface
        self.recipe = recipe
        self.alert = alert
        self.summary_stats = None

        self.title = sw.CardTitle(children=["Dashboard Generation"])

        # Create dashboard dialog
        self.dashboard_dialog = dashboard_dialog

        # Compute button
        self.btn_dashboard = sw.TaskButton(
            cm.dashboard.toolbar.btn.compute.title, small=True, block=True
        )

        # View button (initially disabled)
        self.btn_view_dashboard = TextBtn("View Dashboard", block=True)
        self.btn_view_dashboard.on_event("click", self._open_existing_dashboard)

        self.children = [
            sw.Row(
                children=[
                    sw.Col(children=[self.btn_dashboard], cols=6),
                    sw.Col(children=[self.btn_view_dashboard], cols=6),
                ]
            ),
        ]

        self._configure_dashboard()

    def _configure_dashboard(self):
        """Configure the dashboard computation"""

        def create_dashboard_task():
            def callback(*_):
                task = self.btn_dashboard._task
                if task:
                    self.summary_stats = task.result

                    # Set content and open dialog
                    self.dashboard_dialog.set_results(self.summary_stats)

            return self.gee_interface.create_task(
                func=get_summary_statistics_async,
                key="create_dashboard_task",
                on_done=callback,
                on_error=lambda e: self.alert.add_msg(str(e), type_="error"),
            )

        self.btn_dashboard.configure(
            task_factory=create_dashboard_task,
            start_args=(self.gee_interface, self.recipe),
        )

    def _open_existing_dashboard(self, *_):
        """Open dashboard with existing results"""
        if self.summary_stats:
            self.dashboard_dialog.set_results(self.summary_stats)

        else:
            self.alert.add_msg(
                "No dashboard results available. Please compute first.", type_="warning"
            )
            return

    def reset(self):
        """Reset component state"""
        self.summary_stats = None
        self.dashboard_dialog.close_dialog()


class CompareComponent(sw.Layout):
    """Component for scenario comparison"""

    def __init__(
        self,
        gee_interface: GEEInterface,
        recipe: Recipe,
        alert: Alert,
        map_,
        dashboard_dialog: DashboardDialog,
        sepal_session=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.gee_interface = gee_interface
        self.recipe = recipe
        self.alert = alert
        self.map_ = map_
        self.dashboard_dialog = dashboard_dialog
        self.sepal_session = sepal_session

        self.title = sw.CardTitle(children=["Scenario Comparison"])

        self.btn_compare = TextBtn("Compare Scenarios", block=True)

        self.compare_dialog = cw.CompareScenariosDialog(
            type_="chart",
            alert=self.alert,
            sepal_session=self.sepal_session,
            gee_interface=self.gee_interface,
            map_=self.map_,
            dashboard_dialog=self.dashboard_dialog,
        )

        self.btn_compare.on_event("click", lambda *_: self.compare_dialog.open_dialog())

        self.children = [
            self.btn_compare,
            self.compare_dialog,
        ]
