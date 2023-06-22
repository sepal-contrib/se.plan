from sepal_ui import mapping as sm


class CustomMap(sm.SepalMap):
    def zoom_bounds(self, bounds, zoom_out=1):
        """Use the build in fit_bounds method instead of our custom implementation.

        Args:
            bounds ([coordinates]): coordinates corners as minx, miny, maxx, maxy in EPSG:4326
            zoom_out (int) (optional): Zoom out the bounding zoom

        Return:
            self
        """
        minx, miny, maxx, maxy = bounds
        self.fit_bounds([[miny, minx], [maxy, maxx]])

        return self
