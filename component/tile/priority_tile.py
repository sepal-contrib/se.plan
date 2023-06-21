from traitlets import HasTraits, Unicode
import json

from sepal_ui import sepalwidgets as sw
from traitlets import link

from component import widget as cw
from component.message import cm


class PriorityTile(sw.Tile, HasTraits):
    custom_v_model = Unicode().tag(sync=True)

    def __init__(self, **kwargs):
        # name the tile
        title = cm.benefits.title
        id_ = "nested_widget"

        # create the table
        self.table = cw.PriorityTable()

        # build the tile
        super().__init__(id_, title, inputs=[self.table], **kwargs)

        self.v_model = json.dumps(self.table._DEFAULT_V_MODEL)

        # hide the borders
        self.children[0].elevation = 0

        # link the widgets to the tile
        link((self, "v_model"), (self.table, "v_model"))
