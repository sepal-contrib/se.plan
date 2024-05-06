from sepal_ui.aoi.aoi_view import AoiView

from component.model.aoi_model import SeplanAoi


class SeplanAoiView(AoiView):
    def __init__(self, model: SeplanAoi, **kwargs: dict):
        kwargs.update(
            {
                "methods": ["-POINTS"],
                "class_": "d-block pa-2 py-4",
                "min_width": "462px",
                "max_width": "462px",
                "model": model.aoi_model,
            }
        )

        super().__init__(**kwargs)

        self.btn.small = True

        model.observe(self.update_view, "set_map")
        model.observe(self.reset_view, "reset_view")

    def update_view(self, *args):
        """Update the view when the feature collection is updated."""
        self.btn.fire_event("click", None)

    def reset_view(self, *args):
        """Reset the view when the feature collection is updated."""
        # I have to do this wrapper to avoid changing the sepal_ui model which
        # not receives any extra argument
        self.reset()
