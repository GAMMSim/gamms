from gamms.typing.sensor_engine import SensorType, ISensor, ISensorEngine
from gamms.typing.context import IContext
from typing import Any, Dict

class NeighborSensor(ISensor):
    def __init__(self, id, type, nodes, edges):
        self.id = id
        self.type = type
        self.nodes = nodes
        self.edges = edges
        self.data = []
    
    def sense(self, node_id: int) -> None:
        nearest_neighbors = {node_id,}
        for edge in self.edges.values():
            if edge.source == node_id:
                nearest_neighbors.add(edge.target)
                        
        self.data = list(nearest_neighbors)
    
    def update(self, data: Dict[str, Any]) -> None:
        return 

class MapSensor(ISensor):
    def __init__(self, id, type, nodes, edges):
        self.id = id
        self.type = type
        self.nodes = nodes
        self.edges = edges
        self.data = ((), ())
    
    def sense(self, node_id: int) -> None:
        self.data = (self.nodes, self.edges)
    
    def update(self, data: Dict[str, Any]) -> None:
        return
    
class AgentSensor(ISensor):
    def __init__(self, id, type, agent):
        self.id = id
        self.type = type
        self.agent = agent
        self.data = {}
    
    def sense(self, node_id: int) -> None:
        agent_data = {}
        for agent in self.agent.create_iter():
            agent_data[agent.name] = agent.current_node_id
        self.data = agent_data
    
    def update(self, data: Dict[str, Any]) -> None:
        return 
    
class SensorEngine(ISensorEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx  
        self.sensors = {}
    def create_sensor(self, id, type: SensorType, **kwargs):
        if type == SensorType.NEIGHBOR:
            sensor = NeighborSensor(id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.MAP:
            sensor = MapSensor(id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.AGENT:
            sensor = AgentSensor(id, type, self.ctx.agent)
        else:
            raise ValueError("Invalid sensor type")
        self.sensors[id] = sensor
        return sensor
    
    def get_sensor(self, id):
        return self.sensors[id]
    
    def terminate(self):
        return