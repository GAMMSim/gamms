from gamms.typing import (
    IArtist,
    IContext,
    IVisualizationEngine,
    ColorType
)
from gamms.typing.opcodes import OpCodes
from gamms.VisualizationEngine.artist import Artist
from gamms.VisualizationEngine import Color

from typing import Dict, Any, List, Tuple, Callable, cast, Union

class NoEngine(IVisualizationEngine):
    def __init__(self, ctx: IContext, **kwargs: Dict[str, Any]) -> None:
        self.ctx = ctx
    
    def set_graph_visual(self, **kwargs: Dict[str, Any]) -> IArtist:
        dummy = cast(Callable[[IContext, Dict[str, Any]], None], lambda ctx, data: None)
        return Artist(self.ctx , dummy, layer=10)
    
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
    
    def human_input(self, agent_name: str, state: Dict[str, Any]) -> int:
        return state["curr_pos"]
    
    def terminate(self):
        return

    def render_text(self, text: str, x: float, y: float, color: ColorType = Color.Black, perform_culling_test: bool=True):
        return

    def render_rectangle(self, x: float, y: float, width: float, height: float, color: ColorType = Color.Black,
                         perform_culling_test: bool=True):
        return

    def render_circle(self, x: float, y: float, radius: float, color: ColorType = Color.Black,
                      perform_culling_test: bool=True):
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
    
    def render_layer(self, layer_id: int) -> None:
        return