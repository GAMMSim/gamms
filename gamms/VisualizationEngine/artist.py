from gamms.typing import IArtist, ArtistType, IContext
from gamms.VisualizationEngine.default_drawers import render_circle, render_rectangle
from gamms.VisualizationEngine import Shape
from typing import Callable, Union, Dict, Any

class Artist(IArtist):
    def __init__(self, ctx: IContext, drawer: Union[Callable[[IContext, Dict[str, Any]], None], Shape], layer: int = 30):
        self.data = {}

        self._ctx = ctx
        self._layer = layer
        self._layer_dirty = False
        self._visible = True
        self._will_draw = True
        self._artist_type = ArtistType.GENERAL
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

    def set_layer(self, layer: int):
        if self._layer == layer:
            return

        self._layer = layer
        self._layer_dirty = True

    def get_layer(self) -> int:
        return self._layer

    def set_visible(self, visible: bool):
        self._visible = visible

    def get_visible(self) -> bool:
        return self._visible

    def set_drawer(self, drawer: Callable[[IContext, Dict[str, Any]], None]):
        self._drawer = drawer

    def get_drawer(self) -> Callable[[IContext, Dict[str, Any]], None]:
        return self._drawer

    def get_will_draw(self) -> bool:
        return self._will_draw

    def set_will_draw(self, will_draw: bool):
        self._will_draw = will_draw

    def get_artist_type(self) -> ArtistType:
        return self._artist_type

    def set_artist_type(self, artist_type: ArtistType):
        self._artist_type = artist_type

    def draw(self):
        try:
            self._drawer(self._ctx, self.data)
        except Exception as e:
            self._ctx.logger.error(f"Error drawing artist: {e}")
            self._ctx.logger.debug(f"Artist data: {self.data}")