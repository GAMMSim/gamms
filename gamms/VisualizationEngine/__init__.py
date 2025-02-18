from enum import Enum

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


class Space:
    World = 0
    Screen = 1
    Viewport = 2

import sys
import importlib.util

def lazy(fullname):
  try:
    return sys.modules[fullname]
  except KeyError:
    spec = importlib.util.find_spec(fullname)
    module = importlib.util.module_from_spec(spec)
    loader = importlib.util.LazyLoader(spec.loader)
    # Make module with proper locking and get it inserted into sys.modules.
    loader.exec_module(module)
    return module

from gamms.VisualizationEngine import agent_visual, graph_visual
from gamms.VisualizationEngine import no_engine, pygame_engine