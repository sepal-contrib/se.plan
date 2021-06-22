from sepal_ui import sepalwidgets as sw 
import ipyvuetify as v 

class CustomAoiDialog(v.Dialog):
    
    def __init__(self):
        
        self.feature = None
        
        self.w_name = v.TextField(
            label = "Sub aoi name",
            v_model = None
        )
        
        self.btn = sw.Btn("validate", "mdi-check")
        
        card = v.Card(
            class_="ma-5",
            children = [
                v.CardTitle(children = ["Select sub AOI name"]),
                v.CardText(children = [self.w_name]),
                v.CardActions(children = [self.btn])
            ]
        )
        
        # init the dialog 
        super().__init__(
            persistent = True,
            value = False,
            max_width = '700px',
            children = [card]
        )
        
        # add js behavior 
        self.btn.on_event('click', self._on_click)
        
    def _on_click(self, widget, data, event):

        # close the dialog
        # it will trigger the saving
        self.value = False

        return self

    def update_aoi(self, geo_json, index):
        """read the aoi and give an default name"""

        # update 
        self.feature = geo_json
        self.w_name.v_model = f"sub AOI {index}"

        # show 
        self.value = True
        
        return self
            