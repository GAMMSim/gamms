class Camera:
    def __init__(self, visualization_engine: "PygameVisualizationEngine", x=0, y=0, size=5):
        self._x = x
        self._y = y
        self._size = size

        self._visualization_engine = visualization_engine

    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value: float):
        self._x = value

    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value: float):
        self._y = value

    @property
    def size(self):
        """
        The orthographic size of the camera represents half the width of the camera view.

        Returns:
            float: The orthographic size.
        """
        return self._size
    
    @property
    def size_y(self):
        """
        The orthographic size of the camera represents half the height of the camera view.

        Returns:
            float: The verticle orthographic size.
        """
        return self._size / self.aspect_ratio
    
    @size.setter
    def size(self, value: float):
        self._size = value

    @property
    def visualization_engine(self):
        return self._visualization_engine
    
    @property
    def aspect_ratio(self):
        return self.visualization_engine.width / self.visualization_engine.height
    
    def world_to_screen_scale(self, world_size: float) -> float:
        """
        Transforms a world size to a screen size.
        """
        return world_size / self.size * self.visualization_engine.width
    
    def screen_to_world_scale(self, screen_size: float) -> float:
        """
        Transforms a screen size to a world size.
        """
        return screen_size / self.visualization_engine.width * self.size
    
    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a world coordinate to a screen coordinate.
        """
        screen_x = (x + self.size) / (2 * self.size) * self.visualization_engine.width
        screen_y = (-y + self.size_y) / (2 * self.size_y) * self.visualization_engine.height
        return screen_x, screen_y
    
    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a screen coordinate to a world coordinate.
        """
        world_x = x / self.visualization_engine.width * 2 * self.size - self.size
        world_y = -y / self.visualization_engine.height * 2 * self.size_y + self.size_y
        return world_x, world_y
    
    def viewport_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a viewport coordinate to a screen coordinate.
        """
        screen_x = x * self.visualization_engine.width
        screen_y = y * self.visualization_engine.height
        return screen_x, screen_y
    
    def viewport_to_screen_scale(self, viewport_size: float) -> float:
        """
        Transforms a viewport size to a screen size.
        """
        return viewport_size * self.visualization_engine.width
    
    def screen_to_viewport_scale(self, screen_size: float) -> float:
        """
        Transforms a screen size to a viewport size.
        """
        return screen_size / self.visualization_engine.width
    
    def screen_to_viewport(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a screen coordinate to a viewport coordinate.
        """
        viewport_x = x / self.visualization_engine.width
        viewport_y = y / self.visualization_engine.height
        return viewport_x, viewport_y