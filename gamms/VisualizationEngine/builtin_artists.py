from dataclasses import dataclass, field

from typing import Tuple, List, Dict, Optional

from gamms.typing import ColorType

@dataclass
class Circle:
    """
    Contains all necessary data for drawing a circle.

    Attributes:
        x (float): The x-coordinate of the circle's center.
        y (float): The y-coordinate of the circle's center.
        radius (float): The radius of the circle.
    """
    x: float
    y: float
    radius: float


@dataclass
class Rectangle:
    """
    Contains all necessary data for drawing a rectangle.

    Attributes:
        x (float): The x-coordinate of the rectangle's center.
        y (float): The y-coordinate of the rectangle's center.
        width (float): The width of the rectangle.
        height (float): The height of the rectangle.
    """
    x: float
    y: float
    width: float
    height: float


@dataclass
class AgentData:
    """
    Contains all necessary data for drawing an agent.

    Attributes:
        name (str): The name of the agent.
        color (ColorType): The color of the agent.
        size (float): The size of the agent.
        current_position (Optional[Tuple[float, float]]): The current position of the agent.
    """
    name: str
    color: ColorType
    size: float
    current_position: Optional[Tuple[float, float]] = field(default=None, init=False)


@dataclass
class GraphData:
    """
    Contains all necessary data for drawing a graph

    Attributes:
        node_color (ColorType): The color of the nodes in the graph.
        edge_color (ColorType): The color of the edges in the graph.
        draw_id (bool): Whether to draw the node IDs.
    """
    node_color: ColorType
    node_size: float
    edge_color: ColorType
    draw_id: bool
    edge_line_points: Dict[int, List[Tuple[float, float]]] = field(default_factory=dict)

@dataclass
class LabelData:
    """Contains all necessary data for drawing a label.
    Attributes:
        text (str): The text of the label.
        color (Optional[ColorType]): The color of the label text.
        size (Optional[int]): The font size of the label text.
        offset (Tuple[float, float]): The offset of the label.
        visible (bool): Whether the label is visible."""
    text: str
    color: Optional[ColorType] = None
    size: Optional[int] = None
    offset: Tuple[float, float] = (0.0, 0.0)
    visible: bool = True
