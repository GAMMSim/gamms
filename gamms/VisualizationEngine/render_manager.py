from gamms.typing import ArtistType, IContext, IArtist

from typing import Set, Dict, List, Optional, Tuple


class RenderManager:
    def __init__(self, ctx: IContext, camera_x: float, camera_y: float, camera_size: float, screen_width: int, screen_height: int):
        self.ctx = ctx

        self._screen_width = screen_width
        self._screen_height = screen_height
        self._aspect_ratio = self._screen_width / self._screen_height

        self._camera_x = int(camera_x)
        self._camera_y = int(camera_y)
        self._camera_size = camera_size
        self._camera_size_y = camera_size / self.aspect_ratio

        self._update_bounds()

        self._artists: Dict[str, IArtist] = {}
        # This will call drawer on all artists in the respective layer
        self._layer_artists: Dict[int, List[str]] = {}
        self._graph_layers: Set[int] = set()
        self._current_drawing_artist: Optional[IArtist] = None

        self._default_origin = (0, 0)
        self._surface_size = 0

    def _update_bounds(self):
        self._bound_left = -self.camera_size + self.camera_x
        self._bound_right = self.camera_size + self.camera_x
        self._bound_top = -self.camera_size_y + self.camera_y
        self._bound_bottom = self.camera_size_y + self.camera_y

    def set_origin(self, x: float, y: float, graph_width: float, graph_height: float):
        self.camera_x = int(x)
        self.camera_y = int(y)
        self._default_origin = (self.camera_x, self.camera_y)
        self._surface_size = max(graph_width, graph_height) + 200
 
    @property
    def camera_x(self):
        return self._camera_x
    
    @camera_x.setter
    def camera_x(self, value: float):
        self._camera_x = value
        self._update_bounds()

    @property
    def camera_y(self):
        return self._camera_y
    
    @camera_y.setter
    def camera_y(self, value: float):
        self._camera_y = value
        self._update_bounds()

    @property
    def camera_size(self):
        """
        The orthographic size of the camera represents half the width of the camera view.

        Returns:
            float: The orthographic size.
        """
        return self._camera_size
    
    @camera_size.setter
    def camera_size(self, value: float):
        self._camera_size = value
        self._camera_size_y = self.camera_size / self.aspect_ratio
        self._update_bounds()
    
    @property
    def camera_size_y(self):
        """
        The orthographic size of the camera represents half the height of the camera view.

        Returns:
            float: The vertical orthographic size.
        """
        return self._camera_size_y
    
    @property
    def screen_width(self):
        return self._screen_width

    @screen_width.setter
    def screen_width(self, value: int):
        self._screen_width = value
        self._aspect_ratio = self._screen_width / self._screen_height
    
    @property
    def screen_height(self):
        return self._screen_height

    @screen_height.setter
    def screen_height(self, value: int):
        self._screen_height = value
        self._aspect_ratio = self._screen_width / self._screen_height
    
    @property
    def aspect_ratio(self):
        return self._aspect_ratio

    @property
    def current_drawing_artist(self):
        return self._current_drawing_artist

    def world_to_screen_scale(self, world_size: float) -> float:
        """
        Transforms a world size to a screen size.
        """
        return world_size / (2 * self.camera_size) * self.screen_width
    
    def screen_to_world_scale(self, screen_size: float) -> float:
        """
        Transforms a screen size to a world size.
        """
        return screen_size / self.screen_width * self.camera_size
    
    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transforms a world coordinate to a screen coordinate.
        """
        x -= self.camera_x
        y -= self.camera_y
        screen_x = (x + self.camera_size) / (2 * self.camera_size) * self.screen_width
        screen_y = (-y + self.camera_size_y) / (2 * self.camera_size_y) * self.screen_height
        return screen_x, screen_y
    
    def screen_to_world(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transforms a screen coordinate to a world coordinate.
        """
        world_x = x / self.screen_width * 2 * self.camera_size - self.camera_size
        world_y = -y / self.screen_height * 2 * self.camera_size_y + self.camera_size_y
        return world_x, world_y
    
    def viewport_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transforms a viewport coordinate to a screen coordinate.
        """
        screen_x = x * self.screen_width
        screen_y = y * self.screen_height
        return screen_x, screen_y
    
    def screen_to_viewport(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transforms a screen coordinate to a viewport coordinate.
        """
        viewport_x = x / self.screen_width
        viewport_y = y / self.screen_height
        return viewport_x, viewport_y
    
    def viewport_to_screen_scale(self, viewport_size: float) -> float:
        """
        Transforms a viewport size to a screen size.
        """
        return viewport_size * self.screen_width
    
    def screen_to_viewport_scale(self, screen_size: float) -> float:
        """
        Transforms a screen size to a viewport size.
        """
        return screen_size / self.screen_width

    def check_circle_culled(self, x: float, y: float, radius: float) -> bool:
        return (x + radius < self._bound_left or x - radius > self._bound_right or
                y + radius < self._bound_top or y - radius > self._bound_bottom)

    def check_rectangle_culled(self, x: float, y: float, width: float, height: float) -> bool:
        return (x - width / 2 > self._bound_right or x + width / 2 < self._bound_left or
                y - height / 2 > self._bound_bottom or y + height / 2 < self._bound_top)

    def check_line_culled(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        return (x1 < self._bound_left and x2 < self._bound_left or x1 > self._bound_right and x2 > self._bound_right or
                y1 < self._bound_top and y2 < self._bound_top or y1 > self._bound_bottom and y2 > self._bound_bottom)

    def check_lines_culled(self, points: List[Tuple[float, float]]) -> bool:
        source = points[0]
        target = points[-1]
        return self.check_line_culled(source[0], source[1], target[0], target[1])

    def check_polygon_culled(self, points: List[Tuple[float, float]]) -> bool:
        for point in points:
            if self._bound_left <= point[0] <= self._bound_right and self._bound_top <= point[1] <= self._bound_bottom:
                return False

        return True

    def add_artist(self, name: str, artist: IArtist) -> None:
        """
        Add an artist to the render manager. An artist can draw one or more shapes on the screen and may have a customized drawer.

        Args:
            name (str): The unique name of the artist.
            artist (IArtist): The artist to add.
        """
        self._artists[name] = artist

        # If layer is specified, will add to list. 
        if artist.get_layer() not in self._layer_artists:
            self._layer_artists[artist.get_layer()] = [name]
            self._layer_artists = {k: self._layer_artists[k] for k in sorted(self._layer_artists.keys())}
        else:
            self._layer_artists[artist.get_layer()].append(name)

        if artist.get_artist_type() == ArtistType.GRAPH:
            self._graph_layers.add(artist.get_layer())

    def remove_artist(self, name: str):
        """
        Remove an artist from the render manager.

        Args:
            name (str): The unique name of the artist to remove.
        """
        if name in self._artists:
            artist = self._artists[name]
            index = self._layer_artists[artist.get_layer()].index(name)
            del self._layer_artists[artist.get_layer()][index]
            del self._artists[name]
        else:
            print(f"Warning: Artist {name} not found.")

    def rebuild_artist_layer(self):
        self._layer_artists.clear()
        self._graph_layers.clear()
        for name, artist in self._artists.items():
            if artist.get_layer() not in self._layer_artists:
                self._layer_artists[artist.get_layer()] = [name]
            else:
                self._layer_artists[artist.get_layer()].append(name)

            if artist.get_artist_type() == ArtistType.GRAPH:
                self._graph_layers.add(artist.get_layer())

        self._layer_artists = {k: self._layer_artists[k] for k in sorted(self._layer_artists.keys())}

    def render_single_artist(self, artist_name: str):
        artist = self._artists.get(artist_name, None)
        if artist is None:
            self.ctx.logger.warning(f"Artist {artist_name} not found.")
            return

        self._current_drawing_artist = artist
        artist.draw()
        self._current_drawing_artist = None

    def handle_render(self):
        """
        Render all render nodes in the render manager. This should be called every frame from the pygame engine to update the visualization.

        Raises:
            NotImplementedError: If the shape of a render node is not implemented and a custom drawer is not provided.
        """
        if any(artist.layer_dirty for artist in self._artists.values()):
            self.rebuild_artist_layer()
            for artist in self._artists.values():
                artist.layer_dirty = False

        rendered_layers: Set[int] = set()
        for layer, artist_name_list in self._layer_artists.items():
            for artist_name in artist_name_list:
                artist = self._artists[artist_name]
                if not artist.get_visible():
                    continue

                if not artist.get_will_draw():
                    if artist.get_artist_type() == ArtistType.GRAPH and layer not in rendered_layers:
                        self.ctx.visual.render_layer(layer)
                        rendered_layers.add(layer)
                    continue

                self._current_drawing_artist = artist
                artist.draw()
                self._current_drawing_artist = None