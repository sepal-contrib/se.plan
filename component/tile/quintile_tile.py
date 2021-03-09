from sepal_ui import sepalwidgets as sw
import ipyvuetify as v 

from component.message import cm
from component import widget as cw

class QuintileTile(sw.Tile):
    
    def __init__(self, io):
        
        # gather io 
        self.io = io
        
        # create the widgets 
        self.asset = sw.AssetSelect()
        mkd = sw.Markdown('  \n'.join(cm.quintile.txt))
        self.clip = cw.LinkDialog()
        
        output = sw.Alert() \
            .bind(self.asset, self.io, 'asset')
        
        super().__init__(
            id_ = "quintile_tile",
            title = cm.quintile.title,
            inputs = [mkd, self.asset, self.clip],
            btn = sw.Btn(cm.quintile.btn),
            output = output
        )
        
        # js behaviour
        self.btn.on_event('click', self._to_quintile)
        
    def _to_quintile(self, widget, event, data):
        """transform the user image into a quintile image"""
        
        widget.toggle_loading()
        
        # check inputs 
        if not self.output.check_inputs(self.io.asset, cm.quintile.no_asset): return widget.toggle_loading()
        
        # start the process 
        try:
            self.output.add_live_msg('I will do something one day')
            
            # create the quintile asset 
            # image = cs.compute_quintile(io.asset, self.output)
            
            # export it as an asset 
            #io.q_Asset = cs.export_image(image, self.output)
            
            # fire the copy-to-clipboard btn
            # self.clip.fire_dialog(io.q_asset)
            
        except Exception as e: 
            self.output.add_live_msg(str(e), 'error') 
            
        
        widget.toggle_loading()
        
        return self
        
        