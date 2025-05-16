from dataclasses import dataclass, field
from gamms.typing import ColorType
from typing import List, Tuple, Dict, Optional

@dataclass()
class CircleRenderCommandData:
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
class RectangleRenderCommandData:
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
class PolygonRenderCommandData:
    """
    Contains all necessary data for drawing a polygon.

    Attributes:
        points (List[Tuple[float, float]]): A list of points representing the vertices of the polygon.
        color (ColorType): The color of the polygon.
    """
    points: List[Tuple[float, float]]
    color: ColorType

@dataclass()
class LineRenderCommandData:
    """
    Contains all necessary data for drawing a line.

    Attributes:
        x1 (float): The x-coordinate of the start point of the line.
        y1 (float): The y-coordinate of the start point of the line.
        x2 (float): The x-coordinate of the end point of the line.
        y2 (float): The y-coordinate of the end point of the line.
        color (ColorType): The color of the line.
    """
    x1: float
    y1: float
    x2: float
    y2: float
    color: ColorType

@dataclass()
class LineStringRenderCommandData:
    """
    Contains all necessary data for drawing a linestring.

    Attributes:
        points (List[Tuple[float, float]]): A list of points representing the vertices of the linestring.
        color (ColorType): The color of the linestring.
    """
    points: List[Tuple[float, float]]
    color: ColorType
    is_aa: bool

@dataclass()
class TextRenderCommandData:
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