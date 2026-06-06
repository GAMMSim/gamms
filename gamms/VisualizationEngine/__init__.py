from enum import Enum, auto, IntEnum

class Engine(Enum):
    NO_VIS = 0
    PYGAME = 1

class Color:
    White = (255, 255, 255)
    Black = (0, 0, 0)
    Red = (255, 0, 0)
    Green = (0, 255, 0)
    LightGreen = (144, 238, 144)
    Blue = (0, 0, 255)
    Yellow = (255, 255, 0)
    Cyan = (0, 255, 255)
    Magenta = (255, 0, 255)
    Gray = (169, 169, 169)
    LightGray = (211, 211, 211)
    DarkGray = (128, 128, 128)
    Brown = (210, 105, 30)
    Purple = (128, 0, 128)


class Space(IntEnum):
    World = 0
    Screen = 1
    Viewport = 2


class Shape(Enum):
    Circle = auto()
    Rectangle = auto()


SHORT_EDGE_PIXEL_THRESHOLD = 3.0
SKIP_EDGE_PIXEL_THRESHOLD = 1.0
SKIP_NODE_PIXEL_THRESHOLD = 1.0
CACHE_ZOOM_MAX = 1.2


import sys
import importlib

def lazy(name: str):
    import importlib
    module = None

    class _Lazy:
        def _load(self):
            nonlocal module
            if module is None:
                module = importlib.import_module(name)
                self.__dict__.update(module.__dict__)

        def __getattr__(self, attr):
            self._load()
            return getattr(module, attr)

    return _Lazy()

from .artist import Artist, RenderMode
from .no_engine import NoEngine
from .pygame_engine import PygameVisualizationEngine
