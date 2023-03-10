from types import SimpleNamespace

from sepal_ui.mapping import layers_control as lc
from sepal_ui.message import ms
from sepal_ui import sepalwidgets as sw


class LayersControl(lc.LayersControl):
    """overwrite of the layercontrol widget to only support basemaps"""

    def update_table(self, change: dict) -> None:
        """Update the table content."""

        # create another table of basemapLine it should always be a basemap
        # the error raised if you delete the last one is a feature
        bases = [lyr for lyr in self.m.layers if lyr.base is True]
        base_rows = []
        current = next(
            (lyr for lyr in bases if lyr.visible is True), SimpleNamespace(name=None)
        )
        if len(bases) > 0:
            head = [lc.HeaderRow(ms.layer_control.basemap.header)]
            empy_cell = sw.Html(tag="td", children=[" "], attributes={"colspan": 3})
            empty_row = sw.Html(tag="tr", class_="v-no-hever", children=[empy_cell])
            rows = [lc.BaseRow(lyr) for lyr in bases] + [empty_row]
            base_rows = head + rows

        # create a table from these rows and wrap it in the radioGroup
        tbody = sw.Html(tag="tbody", children=base_rows)
        table = sw.SimpleTable(children=[tbody], dense=True, class_="v-no-border")
        self.group = sw.RadioGroup(v_model=current.name, children=[table])

        # set the table as children of the widget
        self.tile.children = [self.group]

        return
