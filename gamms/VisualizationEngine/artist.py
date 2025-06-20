from gamms.typing import IArtist, ArtistType, IContext, IRenderCommand
from gamms.VisualizationEngine.default_drawers import render_circle, render_rectangle
from gamms.VisualizationEngine import Shape
from typing import Callable, Union, Dict, List, Any

class Artist(IArtist):
    def __init__(self, ctx: IContext, drawer: Union[Callable[[IContext, Dict[str, Any]], List[IRenderCommand]], Shape], layer: int = 30):
        self.data = {}

        self._ctx = ctx
        self._layer = layer
        self._layer_dirty = False
        self._visible = True
        self._is_rendering = True
        self._artist_type = ArtistType.GENERAL
        self._render_commands: List[IRenderCommand] = []
        if isinstance(drawer, Shape):
            if drawer == Shape.Circle:
                self._drawer = render_circle
            elif drawer == Shape.Rectangle:
                self._drawer = render_rectangle
            else:
                raise ValueError("Unsupported shape type")
        else:
            self._drawer = drawer

    @property
    def layer_dirty(self) -> bool:
        return self._layer_dirty
    
    @layer_dirty.setter
    def layer_dirty(self, value: bool):
        self._layer_dirty = value

    @property
    def render_commands(self) -> List[IRenderCommand]:
        return self._render_commands

    def set_layer(self, layer: int):
        if self._layer == layer:
            return

        self._layer = layer
        self._layer_dirty = True

    def get_layer(self) -> int:
        return self._layer

    def set_visible(self, visible: bool):
        self._visible = visible

    def is_visible(self) -> bool:
        return self._visible

    def set_drawer(self, drawer: Callable[[IContext, Dict[str, Any]], None]):
        self._drawer = drawer

    def get_drawer(self) -> Callable[[IContext, Dict[str, Any]], None]:
        return self._drawer

    def is_rendering(self) -> bool:
        return self._is_rendering

    def set_rendering(self, is_rendering: bool):
        self._is_rendering = is_rendering

    def get_artist_type(self) -> ArtistType:
        return self._artist_type

    def set_artist_type(self, artist_type: ArtistType):
        self._artist_type = artist_type

    def draw(self, force = False):
        if self._is_rendering and not force:
            return

        try:
            self._render_commands = self._drawer(self._ctx, self.data)
        except Exception as e:
            self._ctx.logger.error(f"Error drawing artist: {e}")
            self._ctx.logger.debug(f"Artist data: {self.data}")

    def clear(self):
        if self._is_rendering:
            return

        self._render_commands.clear()