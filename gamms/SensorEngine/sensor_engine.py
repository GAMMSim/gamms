from gamms.typing.sensor_engine import SensorType, ISensor, ISensorEngine
from gamms.typing.context import IContext
from gamms.typing.opcodes import OpCodes
from typing import Any, Dict


class NeighborSensor(ISensor):
    def __init__(self, ctx, sensor_id, type, nodes, edges):
        self.sensor_id = sensor_id
        self.ctx = ctx
        self.type = type
        self.nodes = nodes
        self.edges = edges
        self.data = []
    
    def data(self):
        return self.data
    
    def sense(self, node_id: int) -> None:
        nearest_neighbors = {node_id,}
        for edge in self.edges.values():
            if edge.source == node_id:
                nearest_neighbors.add(edge.target)
                        
        self.data = list(nearest_neighbors)
    
    def update(self, data: Dict[str, Any]) -> None:
        return 

class MapSensor(ISensor):
    def __init__(self, ctx, sensor_id, type, nodes, edges):
        self.sensor_id = sensor_id
        self.ctx = ctx
        self.type = type
        self.nodes = nodes
        self.edges = edges
        self.data = ((), ())
    
    def data(self):
        return self.data

    def sense(self, node_id: int) -> None:
        self.data = (self.nodes, self.edges)
    
    def update(self, data: Dict[str, Any]) -> None:
        return
    
class AgentSensor(ISensor):
    def __init__(self, ctx,  sensor_id, type, agent):
        self.sensor_id = sensor_id
        self.ctx = ctx
        self.type = type
        self.agent = agent
        self.data = {}
    
    def data(self):
        return self.data
    
    def sense(self, node_id: int) -> None:
        agent_data = {}
        for agent in self.agent.create_iter():
            agent_data[agent._name] = agent.current_node_id
        self.data = agent_data

    def update(self, data: Dict[str, Any]) -> None:
        return 
    
class SensorEngine(ISensorEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx  
        self.sensors = {}
        
    def create_sensor(self, sensor_id, type: SensorType, **kwargs):
        if type == SensorType.NEIGHBOR:
            sensor = NeighborSensor(self.ctx, sensor_id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.MAP:
            sensor = MapSensor(self.ctx, sensor_id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.AGENT:
            sensor = AgentSensor(self.ctx, sensor_id, type, self.ctx.agent)
        else:
            raise ValueError("Invalid sensor type")
        self.sensors[sensor_id] = sensor
        return sensor
    
    def get_sensor(self, sensor_id):
        try:
            return self.sensors[sensor_id]
        except KeyError:
            raise KeyError(f"Sensor {sensor_id} not found.")
    
    def terminate(self):
        return