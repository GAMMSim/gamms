from gamms.typing.sensor_engine import SensorType, ISensor, ISensorEngine
from gamms.typing.context import IContext
from gamms.typing.recorder import OpCodes as op
from typing import Any, Dict


class NeighborSensor(ISensor):
    def __init__(self, ctx, id, type, nodes, edges):
        self.id = id
        self.ctx = ctx
        self.type = type
        self.nodes = nodes
        self.edges = edges
        self.data = []
    
    def data(self):
        return self.data
    
    #setter
    def sense(self, node_id: int) -> None:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=op.NEIGHBOR_SENSOR_SENSE, data=node_id)

        nearest_neighbors = {node_id,}
        for edge in self.edges.values():
            if edge.source == node_id:
                nearest_neighbors.add(edge.target)
                        
        self.data = list(nearest_neighbors)
    
    def update(self, data: Dict[str, Any]) -> None:
        return 

class MapSensor(ISensor):
    def __init__(self, ctx, id, type, nodes, edges):
        self.id = id
        self.ctx = ctx
        self.type = type
        self.nodes = nodes
        self.edges = edges
        self.data = ((), ())
    
    def data(self):
        return self.data

    def sense(self, node_id: int) -> None:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=op.MAP_SENSOR_SENSE, data=node_id)
        self.data = (self.nodes, self.edges)
    
    def update(self, data: Dict[str, Any]) -> None:
        return
    
class AgentSensor(ISensor):
    def __init__(self, ctx,  id, type, agent):
        self.id = id
        self.ctx = ctx
        self.type = type
        self.agent = agent
        self.data = {}
    
    def data(self):
        return self.data
    
    def sense(self, node_id: int) -> None:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=op.AGENT_SENSOR_SENSE, data=node_id)
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
        
    def create_sensor(self, id, type: SensorType, **kwargs):
        if self.ctx.record.record():
            self.ctx.record.write(opCode=op.SENSOR_CREATE, data={"id": id, "type":type, "kwargs":kwargs})
        if type == SensorType.NEIGHBOR:
            sensor = NeighborSensor(self.ctx, id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.MAP:
            sensor = MapSensor(self.ctx, id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.AGENT:
            sensor = AgentSensor(self.ctx, id, type, self.ctx.agent)
        else:
            raise ValueError("Invalid sensor type")
        self.sensors[id] = sensor
        return sensor
    
    def get_sensor(self, id):
        return self.sensors[id]
    
    def terminate(self):
        return