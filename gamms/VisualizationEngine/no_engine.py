from gamms.typing import (
    IArtist,
    IContext,
    IVisualizationEngine,
    ColorType,
    AgentType
)
from gamms.typing.opcodes import OpCodes
from gamms.VisualizationEngine.artist import Artist
from gamms.VisualizationEngine import Color

from typing import Dict, Any, List, Tuple, Callable, Optional, cast, Union

class NoEngine(IVisualizationEngine):
    def __init__(self, ctx: IContext, **kwargs: Dict[str, Any]) -> None:
        self.ctx = ctx
        self._camera_x = 0.0
        self._camera_y = 0.0
        self._camera_size = 0.0
    
    def set_graph_visual(self, **kwargs: Dict[str, Any]) -> IArtist:
        dummy = cast(Callable[[IContext, Dict[str, Any]], None], lambda ctx, data: None)
        return Artist(self.ctx , dummy, layer=10)
    
    def set_obstacle_visual(self, **kwargs: Dict[str, Any]) -> IArtist:
        dummy = cast(Callable[[IContext, Dict[str, Any]], None], lambda ctx, data: None)
        return Artist(self.ctx , dummy, layer=5)
    
    def set_agent_visual(self, name: str, **kwargs: Dict[str, Any]) -> IArtist:
        dummy = cast(Callable[[IContext, Dict[str, Any]], None], lambda ctx, data: None)
        return Artist(self.ctx , dummy, layer=20)
    
    def set_sensor_visual(self, name: str, **kwargs: Dict[str, Any]) -> IArtist:
        dummy = cast(Callable[[IContext, Dict[str, Any]], None], lambda ctx, data: None)
        return Artist(self.ctx , dummy, layer=40)
    
    def add_artist(self, name: str, artist: Union[IArtist, Dict[str, Any]]) -> IArtist:
        if isinstance(artist, dict):
            dummy = cast(Callable[[IContext, Dict[str, Any]], None], lambda ctx, data: None)
            artist = Artist(self.ctx, dummy, layer=30)
            artist.data = artist
        return artist
    
    def remove_artist(self, name: str):
        return

    def simulate(self):
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.SIMULATE, data={})
        return
    
    def human_input(self, agent_name: str, state: Dict[str, Any]) -> Union[int, Tuple[float, float, float]]:
        agent = self.ctx.agent.get_agent(agent_name)
        if agent.type == AgentType.BASIC:
            return state["curr_pos"]
        elif agent.type == AgentType.AERIAL:
            return (0.0, 0.0, 0.0)
        else:
            raise RuntimeError(f"Unknown agent type {agent.type} for agent {agent_name}")
    
    def terminate(self):
        return

    def render_text(self, text: str, x: float, y: float, color: ColorType = Color.Black, perform_culling_test: bool=True):
        return

    def render_rectangle(self, x: float, y: float, width: float, height: float, color: ColorType = Color.Black,
                         perform_culling_test: bool=True):
        return

    def render_circle(self, x: float, y: float, radius: float, color: ColorType = Color.Black, width: int = 0,
                      perform_culling_test: bool = True):
        return

    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: ColorType = Color.Black,
                    width: int=1, is_aa: bool=False, perform_culling_test: bool=True, force_no_aa: bool = False):
        return

    def render_linestring(self, points: List[Tuple[float, float]], color: ColorType =Color.Black, width: int=1, closed: bool = False,
                     is_aa: bool=False, perform_culling_test: bool=True):
        return

    def render_polygon(self, points: List[Tuple[float, float]], color: ColorType = Color.Black, width: int=0,
                       perform_culling_test: bool=True):
        return

    def render_image(self, x: float, y: float, image: Any, size: float, angle: float = 0.0,
                     perform_culling_test: bool = True):
        return
    
    def render_layer(self, layer_id: int) -> None:
        return

    def get_viewport(self) -> Optional[Tuple[float, float, float, float, float]]:
        return None

    def get_camera(self) -> Tuple[float, float, float]:
        return (self._camera_x, self._camera_y, self._camera_size)

    def set_camera(self, x: float, y: float, size: float) -> None:
        self._camera_x = float(x)
        self._camera_y = float(y)
        self._camera_size = max(float(size), 0.0)

    def pan(self, dx: float, dy: float) -> None:
        self._camera_x += float(dx)
        self._camera_y += float(dy)

    def zoom(self, factor: float, center: Optional[Tuple[float, float]] = None) -> None:
        if center is None:
            cx, cy = self._camera_x, self._camera_y
        else:
            cx, cy = float(center[0]), float(center[1])
        factor = float(factor)
        self._camera_x = cx + (self._camera_x - cx) * factor
        self._camera_y = cy + (self._camera_y - cy) * factor
        self._camera_size = max(self._camera_size * factor, 0.0)

    def zoom_to_fit(self, margin: float = 1.1) -> None:
        x_list: List[float] = []
        y_list: List[float] = []
        for node_id in self.ctx.graph.graph.get_nodes():
            node = self.ctx.graph.graph.get_node(node_id)
            x_list.append(node.x)
            y_list.append(node.y)
        if x_list:
            self._camera_x = (min(x_list) + max(x_list)) / 2
            self._camera_y = (min(y_list) + max(y_list)) / 2
            self._camera_size = max((max(x_list) - min(x_list)) * margin,
                                    (max(y_list) - min(y_list)) * margin, 0.0)