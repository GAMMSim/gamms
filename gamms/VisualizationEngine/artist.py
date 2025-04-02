from gamms.typing.artist import IArtist, ArtistType
from gamms.context import Context


class Artist(IArtist):
    def __init__(self, ctx: Context, drawer: callable, layer: int = 30):
        self.data = {}

        self._ctx = ctx
        self._layer = layer
        self._visible = True
        self._will_draw = True
        self._artist_type = ArtistType.GENERAL
        self._drawer = drawer

    def set_layer(self, layer):
        self._layer = layer
        self._ctx.visual.on_artist_change_layer()

    def get_layer(self):
        return self._layer

    def set_visible(self, visible):
        self._visible = visible

    def get_visible(self):
        return self._visible

    def set_drawer(self, drawer):
        self._drawer = drawer

    def get_drawer(self):
        return self._drawer

    def get_will_draw(self):
        return self._will_draw

    def set_will_draw(self, will_draw):
        self._will_draw = will_draw

    def get_artist_type(self):
        return self._artist_type

    def set_artist_type(self, artist_type):
        self._artist_type = artist_type

    def draw(self):
        self._drawer(self._ctx, self)