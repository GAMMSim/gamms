from gamms.typing import IVisualizationEngine
from gamms.context import Context

from typing import Dict, Any

class NoEngine(IVisualizationEngine):
    def __init__(self, ctx: Context):
        self.ctx = ctx
    
    def set_graph_visual(self, **kwargs):
        return
    
    def set_agent_visual(self, agent_name: str, **kwargs):
        return
    
    def add_artist(self, name:str, data: Dict[str, Any]):
        return
    
    def remove_artist(self, name: str):
        return

    def simulate(self):
        return
    
    def human_input(self, name: str, state: Dict[str, Any]):
        state['action'] = state['current_node_id']
        return
    
    def terminate(self):
        return