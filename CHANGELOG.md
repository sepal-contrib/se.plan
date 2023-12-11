## 1.2.0 (2023-12-11)

### Feat

- use sepal_ui==2.17 to avoid conflicts with ipyleaflet
- remove pinned requirements. use convenient sepal_ui version

### Fix

- display meaningful error message when resolution is too coarse. related with #220
- **aoi_model**: imports gaul_database from pygaul

### Refactor

- **decorator**: drop debug arg

## 1.1.1 (2023-09-25)

### Refactor

- **__version__.py**: remove __version__.py file and use [[project.version]] in pypoject.toml
- move __version__ file to root

## 1.1.0 (2023-09-21)

### Feat

- allow usage of same layer multiple times. - it will be useful when using continuous layers, i.e. multiple ranges can be selected. - instead of rendering the dashboard with the hardcoded info from the layers, I will use the one comming from the model, so it will remain interactive.
- allow download of all assets in the questionnaire
- close map info dialog on map if different drawer is used and be sure user has read that
- add waiting message
- set default zooms for map and reset event + center object when indexes are created
- set reset methods to both map and dashboard
- display a message with the full recipe path after saving
- improve recipe status and name display. - set recipe name on top of the app (appbar) - set recipe status after recipe name - update recipe "new_change" trait every time something has been edited.
- render components concurrently and simplify alert state to avoid conflicts with concurrent calls
- render components concurrently and simplify alert state to avoid conflicts with concurrent calls
- open info dialog first time map_tile is opened
- open info dialog first time map_tile is opened
- resize preview map when it is open
- resize preview map when it is open
- catch errors on show_map method
- catch errors on show_map method
- use custom drawers to comunicate with components from app
- define custom legends with css to improve visual style
- only apply the vh to .custom_map maps
- function to display preview maps with colors
- function to display preview maps with colors
- update row data from model
- update row data from model
- add hint message to constraint widgets
- create preview AOI dialog
- WIP, set custom dialog to display individual layers on a map
- atomize mask_image process for testing purposes
- import frontend
- use pure html+css to create legend and add nodata color
- set maps default height
- use venv
- use venv
- simplifly ui workflow
- return recipe to initial state if view fails
- return recipe to initial state if view fails
- remove asset from model if the view fails on its build, display an error
- remove asset from model if the view fails on its build, display an error
- add reset methods to reinitiate all questionnaire models
- add reset methods to reinitiate all questionnaire models
- seplan_aoi improvements: AOI MODEL - new AoiModel inheriting from sepal_ui to add updated trait in the model after set the object. - replace clear attributes event to avoid remove updated trait - replace "name" as trigger trait from seplanaoi I used updated. - set map map event that will be listened by custom view and set after data is imported. - add reset method and add reset_view trait that will be listened by custom aoi view to reset widgets as well AOI VIEW - wrap parent methods to listen model instead to interact directly with the view
- seplan_aoi improvements: AOI MODEL - new AoiModel inheriting from sepal_ui to add updated trait in the model after set the object. - replace clear attributes event to avoid remove updated trait - replace "name" as trigger trait from seplanaoi I used updated. - set map map event that will be listened by custom view and set after data is imported. - add reset method and add reset_view trait that will be listened by custom aoi view to reset widgets as well AOI VIEW - wrap parent methods to listen model instead to interact directly with the view
- catch errors with shared alert
- catch errors with shared alert
- table dialog: - add and remove default assets to w_asset element - use shared alert between components form table - use read only on default compontents
- table dialog: - add and remove default assets to w_asset element - use shared alert between components form table - use read only on default compontents
- fix trash can
- fix trash can
- connect recipe build process with map drawers + rearrange recipe action cards
- improve error handling and error messages
- wrap recipe alert as dialog. Improve message displaying
- stablish recipe tile and view structure
- enhance recipe validation process
- remove traits from recipe model and store them directly in the AlertState widget. Pass alert state to tiles to capture progress messages
- increment the max pixels threshold to get raster values
- use link instead of directional link to update map features from model
- set validation schema for recipe file
- set loaod recipe view
- define draft validation method to recipe json files
- define recipe tile components and set state on tiles to improve loading speed
- recipe
- first draft of recipe object
- link custom map layers with model
- complete weighted average approach on benefits
- add method to update value or weights from model
- define an aoi model that merges all types of aois in the module
- move map info to a dialog
- customize custom aoi dialog - only show add element when new geometry is created - hide no items when there's items in the table - adjust messages and keys
- refactor custom aoi dialog and show current features on map
- clean
- clean
- compile questionaire translation keys into one single file
- allow recreation of widgets when model is instantiated
- improve custom slider widget
- set limits according to the type of data
- improve efficiency. - add/edit/remove only specific rows that were created.
- multi type widget
- add asset type
- add nox file

### Fix

- allow none on recipe. It will happen when the app just start at the beginning
- fix recipe schema
- update seplan_aoi model when model is resetted. - Once the sepal_ui.aoi_model is resetted, we have to update the "sepal_aoi" model so it can remove the feature collection from it and stop propagating it trough all the components"
- remove tooltip on btn menu due to a bug that makes it constantly displayed
- remove tooltip on btn menu due to a bug that makes it constantly displayed
- fix units
- use v.html instead of ipywidgets
- fix order of min max values
- reimports
- use add_layer instead of add because add method doesn't create the key attribute to the layers
- fix constraints method to generate the constraints mask
- set proper schema for primary aoi json file
- typo on import data from models
- typo
- allow none on aoi_name when it is just instantiated
- fix typos
- update the computed indices on the map
- edit constraint
- add the Satellite imagery to the dashboard map
- change the format of the dashboard table
- add legend on the result map
- display the subthemes in the questionnaire Fix #107
- display constraints on the final map Fix #78
- replace establishment by implementation Fix #64
- improve constraints inclusion
- set constraints values to -1when disabled Fix #73
- constraints bug when min is 0
- point to master files
- change warning message

### Refactor

- disable csv exportation
- deactivate load from shape button FTM. It will be integrated later on the geometry menu
- make the alerts persistent
- seplan_aoi has its own upadted trait, there's no need to use the sepal_ui updated one
- remove legacy file
- remove legacy file
- use the average cost per hectare instead of total costs
- use more efficient mask. Inverse continuos mask
- reuse asset_to_image
- rename to close_dialog() to avoid conflicts with parent close() method
- use single parent base dialog
- remove height on layout. It doesn't work
- move set_limits workflow to a separate module, so it can be easily tested
- use same meethod names over different models
- use same meethod names over different models
- remove unused files
- individualize dashboard translation|
- ui management: - define a custom and unique dialog alert to be shared among all components from questionnnaire. - capture errors using wrapped alert - define default layers that cannot be removed and minimun quantity in constraints
- remove unused files
- separate dashboard button from map_tile and move it to dashboard. Create a dashboard toolbar
- invere mask annotation on constraints
- rename tables to rows
- set index page
- create keys for alert recipe messages
- use default ui.ipynb as entry point to app session in nox
- reduce code in action cards. set alert messages on events. set component tile mount_id
- drop legacy files
- clean useless notebooks
- separate get full path method from save method
- rename dashboard to statistics
- isolate batch export functions
- adapt dashboard definition to summary_statistics format
- handle ee_constraint image decomposition from list directly in reduce_constraints function
- define visualization on feature draw instead of doing so in the GeoJSON definition. It will help to store the color of the AOI in the aoi_model
- clean functions and typings
- define get methods to themes
- simplify functions, reduce boilerplate code
- breakdown seplan functions to avoid duplication in dashboard
- link feature_collection from sepal_ui.aoi
- add custom aoi model to seplan builder
- make questionnaire models members of tile
- set custom constraint masks for each data type
- homogenize dialog action buttons
- individualize map. create map toolbar
- move elements as dialogs instead of expansion panels
- definition of questionnaire table as tab container
- reorganize file tree and drop priority var name in favor of benefit
- define a single parent table for all constriants
- docstring members, fully link select widget
- remove validate button
- clean leftover
- improve and simplify set rows method
- refactor new components
- remove importation
- reuse components
- add new components to the model
- refactor costs widgets
- refactor constraint table
- refactor priority table
- fix some small bugs
- drop ipywidgets HTML in favor of v.Html
- adap to sepal_ui.aoi parquet structure
- closes #202
- remove title
