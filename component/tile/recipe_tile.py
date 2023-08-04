# from typing import Literal

# import ipyvuetify as v
# from sepal_ui import sepalwidgets as sw
# from sepal_ui.scripts import utils as su

# from component import parameter as cp
# from component.message import cm
# from component.model import Recipe

# _content = {
#     "new": ["mdi-newspaper-plus", cm.recipe.new.title, cm.recipe.new.desc],
#     "load": ["mdi-upload", cm.recipe.load.title, cm.recipe.load.desc],
#     "save": ["mdi-content-save", cm.recipe.save.title, cm.recipe.save.desc],
# }


# class CardAction(sw.Col):
#     def __init__(self, type_: Literal["new", "load", "save"]):
#         content = _content[type_]
#         # self.class_ = "mx-2"
#         self.cols = 4

#         super().__init__()

#         self.btn = v.Btn(
#             children=[v.Icon(children=[content[0]]), content[1]], variant="text"
#         )

#         self.children = [
#             sw.Card(
#                 hover=True,
#                 max_width=344,
#                 min_width=344,
#                 children=[
#                     sw.CardTitle(children=[content[1]]),
#                     sw.CardSubtitle(children=[content[2]]),
#                     sw.CardActions(children=[self.btn]),
#                 ],
#             )
#         ]

#     def on_event(self, event, handler):
#         self.btn.on_event(event, handler)


# class RecipeTile(sw.Container):
#     def __init__(self):
#         self.attributes = {"_metadata": "recipe_tile"}

#         super().__init__()
#         self.recipe = Recipe()
#         self.alert = sw.Alert()

#         self.card_actions = [CardAction(type_) for type_ in _content.keys()]

#         self.children = (
#             [
#                 sw.Row(
#                     justify="center",
#                     children=[
#                         sw.Col(
#                             cols=12,
#                             children=[
#                                 sw.Html(tag="h1", children=["Welcome to SE.Plan"])
#                             ],
#                         )
#                     ],
#                 )
#             ]
#             + [sw.Row(justify="center", children=self.card_actions)]
#             + [sw.Row(children=[self.alert])]
#         )

#     def new_event(self, *_):
#         """Creates a new recipe from scratch."""

#         # opens new_recipe_dialog
#         # Let the user know that there might be some unsaved changes
#         # let the user select a name
#         # reset or create new values?
#         # I have to reset, because the other components were already created with
#         # the default recipe
#         # We have to make this name fully available to the other components...
#         # Perhaps we can display the name always in the menu bar?

#     def load_event(self, *_):
#         """Opens recipe loader dialog."""

#         # open load_recipe_dialog
#         # let the user search trough the sepal files the recipes in the result folder.
#         # All files containing .json should be listed
#         # Once the value has changed, validate the recipe, do some tests to be sure
#         # all the fields were stored correctly and are there.
#         # if not, user cannot load the recipe and an error message should be displayed,
#         # user cannot close the window by clicking "load", just cancel.

#     def save_event(self, *_):
#         """Saves the current state of the recipe."""

#         # just save the current recipe (get all the values from Recipe) and use the
#         # same name of the session.
#         # If the recipe already exists, ask the user if he wants to overwrite it, or not?

#         # I can also create a switch button to overwrite the current file.


# class LoadDialog(v.Dialog):
#     """
#     Dialog to save a recipe as json file the content of a ClassTable data table.

#     Args:
#         table (ClassTable): Table linked with dialog
#         out_path (str): Folder path to store table content

#     Attributes:
#         reload (Int): a traitlet to inform the rest of the app that saving is complete
#         table (ClassTable): Table linked with dialog
#         out_path (str): Folder path to store table content
#         w_file_name (v.TextField): the filename to use in out_path
#         save (sw.Btn): save btn to launch the saving of the table data in the out_path using the filename provided in the widget
#         cancel (sw.Btn): btn to close the dialog and do nothing
#         alert (sw.Alert): an alert to display evolution of the saving process (errors)
#     """

#     reload = Int().tag(sync=True)

#     def __init__(self, table, out_path, **kwargs):
#         # gather the table and saving params
#         self.table = table
#         self.out_path = out_path

#         # set some default parameters
#         self.max_width = 500
#         self.v_model = False

#         # create the widget
#         super().__init__(**kwargs)

#         # build widgets
#         # Create input file widget wrapped in a layout
#         self.input_impact = sw.FileInput(
#             ".json", folder=cp.directory.TRANSITION_DIR, root=dir_.RESULTS_DIR
#         )

#         self.save = sw.Btn(cm.rec.table.save_dialog.btn.save.name)
#         save = sw.Tooltip(
#             self.save,
#             cm.rec.table.save_dialog.btn.save.tooltip,
#             bottom=True,
#             class_="pr-2",
#         )

#         self.cancel = sw.Btn(
#             cm.rec.table.save_dialog.btn.cancel.name, outlined=True, class_="ml-2"
#         )
#         cancel = sw.Tooltip(
#             self.cancel, cm.rec.table.save_dialog.btn.cancel.tooltip, bottom=True
#         )

#         self.alert = sw.Alert(children=["Choose a name for the output"]).show()

#         # assemlble the layout
#         self.children = [
#             v.Card(
#                 class_="pa-4",
#                 children=[
#                     v.CardTitle(children=[cm.rec.table.save_dialog.title]),
#                     self.w_file_name,
#                     self.alert,
#                     save,
#                     cancel,
#                 ],
#             )
#         ]

#         # Create events
#         self.save.on_event("click", self._save)
#         self.cancel.on_event("click", self._cancel)
#         self.w_file_name.on_event("blur", self._normalize_name)
#         self.w_file_name.observe(self._store_info, "v_model")

#     def _store_info(self, change):
#         """Display where will be the file written."""
#         new_val = change["new"]
#         out_file = self.out_path / f"{su.normalize_str(new_val)}.csv"

#         msg = f"Your file will be saved as: {out_file}"

#         if not new_val:
#             msg = "Choose a name for the output"

#         self.alert.add_msg(msg)

#     def show(self):
#         """
#         display the dialog and write down the text in the alert.

#         Return:
#             self
#         """
#         self.v_model = True
#         self.w_file_name.v_model = ""

#         # the message is display after the show so that it's not cut by the display
#         self.alert.add_msg(cm.rec.table.save_dialog.info.format(self.out_path))

#         return self

#     def _normalize_name(self, widget, event, data):
#         """Replace the name with it's normalized version."""
#         # normalized the name
#         widget.v_model = su.normalize_str(widget.v_model)

#         return

#     def _save(self, widget, event, data):
#         """Write current table on a text file."""
#         # set the file name
#         out_file = self.out_path / su.normalize_str(self.w_file_name.v_model)

#         # write each line values but not the id
#         lines = [list(item.values())[1:] for item in self.table.items]
#         txt = [",".join(str(e) for e in ln) + "\n" for ln in lines]
#         out_file.with_suffix(".csv").write_text("".join(txt))

#         # Every time a file is saved, we update the current widget state
#         # so it can be observed by other objects.
#         self.reload += 1

#         self.v_model = False

#         return

#     def _cancel(self, widget, event, data):
#         """hide the widget and do nothing."""
#         self.v_model = False

#         return

#     # def _normalize_name(self, widget, event, data):
#     #     """normalize the recipe name on blur as it will be used everywhere else."""
#     #     widget.v_model is None or su.normalize_str(widget.v_model)

#     #     return self

#     # def _recipe_placeholder(self, change):
#     #     """name the recipe with the date."""
#     #     now = datetime.now()

#     #     self.w_name.v_model = f'recipe_{now.strftime("%Y-%m-%d")}'

#     #     return self

#     # @su.loading_button(debug=True)
#     # def _validate_data(self, widget, event, data):
#     #     """validate the data and release the computation btn."""
#     #     # watch the inputs
#     #     self.layers_recipe.digest_layers(self.layer_model, self.question_model)
#     #     self.layers_recipe.show()

#     #     # save the inputs in a json
#     #     cs.save_recipe(
#     #         self.layer_model, self.aoi_model, self.question_model, self.w_name.v_model
#     #     )

#     #     return self

#     # def load_recipe(self, widget, event, data, path=None):
#     #     """load the recipe file into the different io, then update the display of the table."""
#     #     # check if path is set, if not use the one frome file select
#     #     path = path or self.file_select.v_model

#     #     cs.load_recipe(self.aoi_tile, self.questionnaire_tile, path)
#     #     self.w_name.v_model = Path(path).stem

#     #     # automatically validate them
#     #     self.btn.fire_event("click", None)

#     #     return self
