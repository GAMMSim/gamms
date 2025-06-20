from gamms.VisualizationEngine.render_command_data import *
from gamms.typing import ColorType, RenderOpCode, IRenderCommand
from typing import List, Tuple, Any

class RenderCommand(IRenderCommand):
    """
    This represents an instance of a render command
    """

    def __init__(self, op_code: RenderOpCode, data = None):
        # the operation code for the command
        self._opcode = op_code

        # contains all parameters for this command
        self._data = data

    @property
    def opcode(self) -> RenderOpCode:
        return self._opcode

    @property
    def data(self) -> Any:
        return self._data

    def __str__(self):
        return f"RenderCommand({self.opcode}, {self.data})"

    @staticmethod
    def circle(x: float, y: float, radius: float, color: ColorType, perform_culling_test: bool=True) -> 'RenderCommand':
        """Create a circle render command"""
        cmd = RenderCommand(RenderOpCode.RenderCircle, CircleRenderCommandData(perform_culling_test, x, y, radius, color))
        return cmd

    @staticmethod
    def rectangle(x: float, y: float, width: float, height: float, color: ColorType, perform_culling_test: bool=True) -> 'RenderCommand':
        """Create a rectangle render command"""
        cmd = RenderCommand(RenderOpCode.RenderRectangle, RectangleRenderCommandData(perform_culling_test, x, y, width, height, color))
        return cmd

    @staticmethod
    def polygon(points: List[Tuple[float, float]], color: ColorType, width: float=0, perform_culling_test: bool=True) -> 'RenderCommand':
        """Create a polygon render command"""
        cmd = RenderCommand(RenderOpCode.RenderPolygon, PolygonRenderCommandData(perform_culling_test, points, color, width))
        return cmd

    @staticmethod
    def line(x1: float, y1: float, x2: float, y2: float, color: ColorType, width: float=1.0, is_aa: bool=False, perform_culling_test: bool=True) -> 'RenderCommand':
        """Create a line render command"""
        cmd = RenderCommand(RenderOpCode.RenderLine, LineRenderCommandData(perform_culling_test, x1, y1, x2, y2, color, width, is_aa))
        return cmd

    @staticmethod
    def linestring(points: List[Tuple[float, float]], color: ColorType, width: float=1.0, closed: bool=False, is_aa: bool=True, perform_culling_test: bool=True) -> 'RenderCommand':
        """Create a linestring render command"""
        cmd = RenderCommand(RenderOpCode.RenderLineString, LineStringRenderCommandData(perform_culling_test, points, color, width, closed, is_aa))
        return cmd

    @staticmethod
    def text(x: float, y: float, text: str, color: ColorType, perform_culling_test: bool=True) -> 'RenderCommand':
        """Create a text render command"""
        cmd = RenderCommand(RenderOpCode.RenderText, TextRenderCommandData(perform_culling_test, x, y, text, color))
        return cmd
