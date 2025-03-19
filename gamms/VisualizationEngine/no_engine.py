from gamms.typing import IVisualizationEngine
from gamms.typing import IArtist
from gamms.typing.opcodes import OpCodes
from gamms.context import Context
from gamms.VisualizationEngine.artist import Artist
from gamms.VisualizationEngine import Color, Space

from typing import Dict, Any

class NoEngine(IVisualizationEngine):
    def __init__(self, ctx: Context, **kwargs):
        self.ctx = ctx
    
    def set_graph_visual(self, **kwargs) -> IArtist:
        dummy = lambda ctx, data: None
        return Artist(ctx, dummy, layer=10)
    
    def set_agent_visual(self, agent_name: str, **kwargs) -> IArtist:
        dummy = lambda ctx, data: None
        return Artist(ctx, dummy, layer=20)
    
    def set_sensor_visual(self, sensor_name: str, **kwargs) -> IArtist:
        dummy = lambda ctx, data: None
        return Artist(ctx, dummy, layer=40)
    
    def add_artist(self, name:str, artist: IArtist) -> None:
        return
    
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

    def render_circle(self, x: float, y: float, radius: float, color: tuple=Color.Black, layer = -1,
                      perform_culling_test: bool=True):
        return

    def render_rectangle(self, x: float, y: float, width: float, height: float, color: tuple = Color.Black, layer = -1,
                         perform_culling_test: bool = True):
        return

    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: tuple = Color.Black,
                    width: int = 1, layer = -1, is_aa: bool = False, perform_culling_test: bool = True):
        return

    def render_linestring(self, points: list[tuple[float, float]], color: tuple = Color.Black, width: int = 1, layer = -1, closed=False,
                     is_aa: bool = False, perform_culling_test: bool = True):
        return

    def render_polygon(self, points: list[tuple[float, float]], color: tuple = Color.Black, width: int = 0, layer = -1,
                       perform_culling_test: bool = True):
        return

    def render_text(self, text: str, x: float, y: float, color: tuple = Color.Black, layer = -1, perform_culling_test: bool=True):
        return


    # METHODS TO BE DELETED
    # ONLY FOR BETA v0.2

    def is_waiting_simulation(self) -> bool:
        return False
    
    def is_waiting_input(self) -> bool:
        return False
    
    def on_artist_change_layer(self) -> None:
        return