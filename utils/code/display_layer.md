# Display/Download layer

This code is used to display the layers from the app to the end user. 
By default it points to Uganda and shows the distance to cities layer from OXFORD. 

You can check it clicking this link: https://code.earthengine.google.com/52d13698bd8bb22195d83e0868aaa2a4

To modify the country change the `fao_gaul` variable line 7 by your country number (listed in the Country list section of the documentation). If you want to export this layer, please set the value of `to_export` (line 10) and `to_drive` (line 13) according to your need. Hit the `run` button again to relaunch the computation

The layer can be modified using the url `layer_id` option. Don't forget to sanityse your layer name first (replace "/" and ":" characters):  
https://code.earthengine.google.com/fba463d16baa71edabc8d93f93785ac5?#layer_id=projects%2Fjohn-ee-282116%2Fassets%2Ffao-restoration%2Ffeatures%2Fyields-4326


## Code

```js
/**************************************************************************
*****************    set user params    ***********************************
***************************************************************************/

// Use a FAO GAUL number. 
// Remember that se.plan layers are only define for the 139 countries available in the documentation
var fao_gaul_number = 253

// set to false to prevent any exportation, and true to export 
var to_export = false 

// set to false to export as an asset, and true to export to drive
var to_drive = false

// select the resolution you want to export to
var resolution = 250

// NO CHANGES AFTER THIS LINE
/**************************************************************************
***************************************************************************/

// get the layer_id from url
// default to distance to cities
var layer_id = ui.url.get(
  'layer_id',
  "Oxford/MAP/accessibility_to_cities_2015_v1_0"
)

// load the aoi from FAO GAUL 
var aoi = ee.FeatureCollection("FAO/GAUL/2015/level0")
  .filter(ee.Filter.eq('ADM0_CODE', fao_gaul_number));

// load the layer
var layer = ee.Image(layer_id).select(0).clip(aoi)

var min = layer.reduceRegion({
  reducer: ee.Reducer.min(),
  geometry: aoi,
  bestEffort: true
});

var layer_name = min.keys().getString(0)

var max = layer.reduceRegion({
  reducer: ee.Reducer.max(),
  geometry: aoi,
  bestEffort: true
})

min = min.getNumber(layer_name)
max = max.getNumber(layer_name)

// set up vizualization parameters
var palettes = require('users/gena/packages:palettes');
var palette = palettes.matplotlib.magma[7]; // https://github.com/gee-community/ee-palettes#colorbrewer-sequential

var viz = {'min': min.getInfo(), 'max': max.getInfo(), 'palette': palette}

// display on the map
Map.centerObject(aoi)
Map.addLayer(aoi, {color: 'green'}, 'aoi')
Map.addLayer(layer, viz, 'layer')

// start the exportation task 
if (to_export) {
  
  if (to_drive) {
    
    Export.image.toDrive({
      image: layer,
      description: layer_name.getInfo(),
      scale: resolution,
      region: aoi
    });
    
  } else {
    
    Export.image.toAsset({
      image: layer,
      description: layer_name.getInfo(),
      assetId: layer_name.getInfo(),
      scale: resolution,
      region: aoi
    })
  }
}

/*
 * Legend setup
 */

// Creates a color bar thumbnail image for use in legend from the given color
// palette.
function makeColorBarParams(palette) {
  return {
    bbox: [0, 0, 1, 0.1],
    dimensions: '300x10',
    format: 'png',
    min: 0,
    max: 1,
    palette: palette,
  };
}

// Create the color bar for the legend.
var colorBar = ui.Thumbnail({
  image: ee.Image.pixelLonLat().select(0),
  params: makeColorBarParams(viz.palette),
  style: {stretch: 'horizontal', margin: '0px 8px', maxHeight: '24px'},
});

// Create a panel with three numbers for the legend.
var legendLabels = ui.Panel({
  widgets: [
    ui.Label(viz.min, {margin: '4px 8px'}),
    ui.Label(
        ((viz.max-viz.min) / 2+viz.min),
        {margin: '4px 8px', textAlign: 'center', stretch: 'horizontal'}),
    ui.Label(viz.max, {margin: '4px 8px'})
  ],
  layout: ui.Panel.Layout.flow('horizontal')
});

var legendTitle = ui.Label({
  value: 'Map Legend: ' + layer_name.getInfo(),
  style: {fontWeight: 'bold'}
});

// Add the legendPanel to the map.
var legendPanel = ui.Panel([legendTitle, colorBar, legendLabels]);
Map.add(legendPanel);`
```