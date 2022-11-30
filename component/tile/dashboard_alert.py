from sepal_ui import sepalwidgets as sw

from component.message import cm


class DashboardAlert(sw.Tile):
    def __init__(self):

        super().__init__(
            title="", id_="dashboard_widget", alert=sw.Alert().add_msg(cm.app.banner)
        )
