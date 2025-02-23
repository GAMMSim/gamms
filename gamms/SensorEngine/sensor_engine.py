from gamms.typing.sensor_engine import SensorType, ISensor, ISensorEngine
from gamms.typing.context import IContext
from gamms.typing.opcodes import OpCodes
from typing import Any, Dict
import math
import numpy as np
from scipy.spatial.distance import cdist

def is_within_range(pos1, pos2, sensor_range: float) -> bool:

    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    # Euclidean distance
    return (dx * dx + dy * dy) <= sensor_range * sensor_range

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

class RangeSensor(ISensor):
    def __init__(self, ctx, sensor_id, sensor_type, nodes, sensor_range: float):
        self.sensor_id = sensor_id
        self.ctx = ctx
        self.type = sensor_type  
        self.nodes = nodes       
        self.range = sensor_range 
        self.data = {} 
    
    def data(self):
        return self.data
    
    def sense(self, node_id: int) -> None:
        current_node = self.nodes[node_id]
        current_position = np.array(current_node.position).reshape(1, 2)
        
        node_ids = list(self.nodes.keys())
        positions = np.array([self.nodes[nid].position for nid in node_ids])
        
        distances = cdist(current_position, positions)[0]
        
        in_range_mask = distances <= self.range
        in_range_ids = {node_ids[i] for i, valid in enumerate(in_range_mask) if valid}
        
        in_range_nodes = {nid: self.nodes[nid] for nid in in_range_ids}
        
        self.data = in_range_nodes

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
        elif type == SensorType.RANGE:
            sensor = RangeSensor(self.ctx, sensor_id, type, self.ctx.graph_engine.graph.nodes, range=30)
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