import ipyvuetify as v
from traitlets import Unicode


class RemathTrigger(v.VuetifyTemplate):
    """Trigger voila method to re-render the mathjax content.
    This event
    """

    # load the js file
    template = Unicode(
        """
        <script class='sepal-ui-script'>
            {
                methods: {
                    jupyter_remath(){
                        if (window.renderMathJax){
                            window.renderMathJax()
                        }
                    }
                }
            }
        </script>
        """
    ).tag(sync=True)
    "Unicode: the javascript script to manually trigger the remath event"

    def remath(self):
        """trigger the method."""
        return self.send({"method": "remath"})


remath = RemathTrigger()
