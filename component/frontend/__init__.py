import ipyvuetify as v
from IPython.display import display

display(
    v.VuetifyTemplate(
        template="""
        <style class='sepal-ui-script'>
            .custom_map .jupyter-widgets.leaflet-widgets {
                height: 84vh;
                margin: 0 !important;
            }
            
            .leaflet-sbs-divider, .leaflet-sbs-range {
                z-index: 201 !important;
            }
        </style>
        """
    )
)
