from traitlets import HasTraits, Unicode
import json
from itertools import product
from sepal_ui import sepalwidgets as sw
import ipyvuetify as v
import pandas as pd

from component.message import cm
from component import parameter as cp
from component import widget as cw


class ConstraintTile(sw.Tile, HasTraits):

    _BENEFITS = pd.read_csv(cp.layer_list).fillna("").applymap(str.strip)

    # create custom_v_model as a traitlet
    # the traitlet List cannot be listened to so we're force to use Unicode json instead
    custom_v_model = Unicode("").tag(sync=True)

    def __init__(self, aoi_view, layer_model):

        # get the models
        self.aoi_model = aoi_view.model
        self.layer_model = layer_model

        # name the tile
        title = cm.constraints.title
        id_ = "nested_widget"

        # write a quick explaination
        tile_txt = sw.Markdown(cm.constraints.desc)

        # read the layer list and find the layer information based on the layer name
        layer_list = pd.read_csv(cp.layer_list).fillna("")

        # create the criteria list
        self.criterias = []
        for key, c in cp.criterias.items():

            layer_row = layer_list[layer_list.layer_id == c["layer"]]
            unit = layer_row.unit.values[0]
            header = c["header"]
            value = c["content"]
            layer = c["layer"]
            hint = cm.constraints.info[c["tooltip"]].format(key)

            if value == "BINARY":  # binary criteria
                crit = cw.Binary(key, header, layer=layer, hint=hint)
            elif isinstance(value, list):  # dropdown values
                crit = cw.Dropdown(key, value, header, layer=layer, hint=hint)
            elif value == "RANGE":  # range values
                crit = cw.Range(key, header, unit, layer=layer, hint=hint)

            self.criterias.append(crit)

        # create each expansion-panel content
        self.panels = v.ExpansionPanels(
            focusable=True,
            v_model=None,
            hover=True,
            accordion=True,
            children=[cw.CustomPanel(k, self.criterias) for k in cp.criteria_types],
        )

        # default custom_v_model
        default_v_model = {c.id: c.custom_v_model for c in self.criterias}
        self.custom_v_model = json.dumps(default_v_model)

        # cration of the tile
        super().__init__(id_, title, inputs=[tile_txt, self.panels])

        # hide the tile border
        self.children[0].elevation = 0

        # link the visibility of each criteria to the select widget
        [c.observe(self._on_change, "custom_v_model") for c in self.criterias]
        self.panels.observe(self._on_panel_change, "v_model")
        aoi_view.observe(self._update_constraints, "updated")

    def _update_constraints(self, change):
        """update all the constraints using sliders based on the geometry and the layer they use"""

        # unable constraint selection
        for cp in self.panels.children:
            cp.select.disabled = False
            cp.select.persistent_hint = False
            cp.select.hint = None

        # reevaluate every layer over the AOI with the default layer
        for c in self.criterias:
            if isinstance(c, cw.Range):
                layer_list = self.layer_model.layer_list
                layer = next(l for l in layer_list if l["id"] == c.id)
                asset = layer["layer"]
                unit = layer["unit"]
                geometry = self.aoi_model.feature_collection.geometry()
                c.set_values(geometry, asset, unit)

        return self

    def _reset_constraint(self, change):
        """update the specified constraint if using slider based on the geometry and the layer it uses"""

        if change["new"] == "":
            return self

        for c in self.criterias:
            if c.id == change["new"] and isinstance(c, cw.Range):
                layer_list = self.layer_model.layer_list
                layer = next(l for l in layer_list if l["id"] == c.id)
                asset = layer["layer"]
                unit = layer["unit"]
                geometry = self.aoi_model.feature_collection.geometry()
                c.set_values(geometry, asset, unit)

        return self

    def load_data(self, data):
        """
        load the data from a json string

        Args:
            data (dict): data to load in the panel using the same format as the queltion_model
        """

        # load the data
        data = json.loads(data)

        # update al the constraints component with the new units and ranges
        self._update_constraints(None)

        # activate every criteria via their panels selector
        for p in self.panels.children:
            criterias = []
            for c, (k, v) in product(p.criterias, data.items()):
                if c.id == k and v != -1:
                    c.widget.v_model = v
                    criterias.append(c.name)

            p.select.v_model = criterias
            p.shrunk()

        return self

    def _on_change(self, change):

        # insert the new values in custom_v_model
        tmp = json.loads(self.custom_v_model)
        tmp[change["owner"].id] = change["new"]
        self.custom_v_model = json.dumps(tmp)

        return

    def _on_panel_change(self, change):
        """revaluate each panel title when the v_model of the expansionpanels is changed"""

        # loop in the custom panels
        for i, p in enumerate(self.panels.children):
            p.expand() if i == change["new"] else p.shrunk()

        return self
