from gamms.VisualizationEngine.render_command_data import *
from gamms.typing import ColorType, RenderOpCode
from typing import List, Tuple

class RenderCommand:
    """
    This represents an instance of a render command
    """

    def __init__(self, op_code: RenderOpCode, data = None):
        # the operation code for the command
        self._opcode = op_code

        # contains all parameters for this command
        self.data = data

    @property
    def opcode(self) -> RenderOpCode:
        return self._opcode

    def validate(self) -> int:
        pass

    def __str__(self):
        return f"RenderCommand({self.opcode}, {self.data})"

    @staticmethod
    def circle(x: float, y: float, radius: float, color: ColorType) -> 'RenderCommand':
        """Create a circle render command"""
        cmd = RenderCommand(RenderOpCode.RenderCircle, CircleRenderCommandData(x, y, radius, color))
        return cmd

    @staticmethod
    def rectangle(x: float, y: float, width: float, height: float, color: ColorType) -> 'RenderCommand':
        """Create a rectangle render command"""
        cmd = RenderCommand(RenderOpCode.RenderRectangle, RectangleRenderCommandData(x, y, width, height, color))
        return cmd

    @staticmethod
    def polygon(points: List[Tuple[float, float]], color: ColorType) -> 'RenderCommand':
        """Create a polygon render command"""
        cmd = RenderCommand(RenderOpCode.RenderPolygon, PolygonRenderCommandData(points, color))
        return cmd

    @staticmethod
    def line(x1: float, y1: float, x2: float, y2: float, color: ColorType) -> 'RenderCommand':
        """Create a line render command"""
        cmd = RenderCommand(RenderOpCode.RenderLine, LineRenderCommandData(x1, y1, x2, y2, color))
        return cmd

    @staticmethod
    def linestring(points: List[Tuple[float, float]], color: ColorType, is_aa: bool = True) -> 'RenderCommand':
        """Create a linestring render command"""
        cmd = RenderCommand(RenderOpCode.RenderLineString, LineStringRenderCommandData(points, color, is_aa))
        return cmd

    @staticmethod
    def text(x: float, y: float, text: str, color: ColorType) -> 'RenderCommand':
        """Create a text render command"""
        cmd = RenderCommand(RenderOpCode.RenderText, TextRenderCommandData(x, y, text, color))
        return cmd
