from dataclasses import dataclass, field
from gamms.typing import ColorType
from typing import List, Tuple, Dict, Optional

@dataclass()
class BaseRenderCommandData:
    """
    Base class for all render command data.

    Attributes:
        perform_culling_test (bool): Whether to perform culling test for this render command.
    """
    perform_culling_test: bool

@dataclass()
class CircleRenderCommandData(BaseRenderCommandData):
    """
    Contains all necessary data for drawing a circle.

    Attributes:
        x (float): The x-coordinate of the circle's center.
        y (float): The y-coordinate of the circle's center.
        radius (float): The radius of the circle.
        color (ColorType): The color of the circle.
    """
    x: float
    y: float
    radius: float
    color: ColorType

@dataclass()
class RectangleRenderCommandData(BaseRenderCommandData):
    """
    Contains all necessary data for drawing a rectangle.

    Attributes:
        x (float): The x-coordinate of the rectangle's center.
        y (float): The y-coordinate of the rectangle's center.
        width (float): The width of the rectangle.
        height (float): The height of the rectangle.
        color (ColorType): The color of the rectangle.
    """
    x: float
    y: float
    width: float
    height: float
    color: ColorType

@dataclass()
class PolygonRenderCommandData(BaseRenderCommandData):
    """
    Contains all necessary data for drawing a polygon.

    Attributes:
        points (List[Tuple[float, float]]): A list of points representing the vertices of the polygon.
        color (ColorType): The color of the polygon.
        width (int): The width of the polygon's edges.
    """
    points: List[Tuple[float, float]]
    color: ColorType
    width: int

@dataclass()
class LineRenderCommandData(BaseRenderCommandData):
    """
    Contains all necessary data for drawing a line.

    Attributes:
        x1 (float): The x-coordinate of the start point of the line.
        y1 (float): The y-coordinate of the start point of the line.
        x2 (float): The x-coordinate of the end point of the line.
        y2 (float): The y-coordinate of the end point of the line.
        color (ColorType): The color of the line.
        width (int): The width of the line.
        is_aa (bool): Whether the line should be anti-aliased line.
    """
    x1: float
    y1: float
    x2: float
    y2: float
    color: ColorType
    width: int
    is_aa: bool

@dataclass()
class LineStringRenderCommandData(BaseRenderCommandData):
    """
    Contains all necessary data for drawing a linestring.

    Attributes:
        points (List[Tuple[float, float]]): A list of points representing the vertices of the linestring.
        color (ColorType): The color of the linestring.
        width (int): The width of the linestring.
        closed (bool): Whether the linestring should be closed (i.e., the last point connects to the first).
        is_aa (bool): Whether the linestring should be anti-aliased linestring.
    """
    points: List[Tuple[float, float]]
    color: ColorType
    width: int
    closed: bool
    is_aa: bool

@dataclass()
class TextRenderCommandData(BaseRenderCommandData):
    """
    Contains all necessary data for drawing text.

    Attributes:
        x (float): The x-coordinate of the text's position.
        y (float): The y-coordinate of the text's position.
        text (str): The text to be drawn.
        color (ColorType): The color of the text.
    """
    x: float
    y: float
    text: str
    color: ColorType