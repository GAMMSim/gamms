from gamms.typing.sensor_engine import SensorType, ISensor, ISensorEngine
from gamms.typing.context import IContext
from gamms.typing.opcodes import OpCodes
from typing import Any, Dict, Optional, Type, TypeVar, Callable
_T = TypeVar('_T')
import math
import numpy as np

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
    def __init__(self, ctx, sensor_id, sensor_type, nodes, sensor_range: float, fov: float, orientation: float):
        """
        Acts as a map sensor (if sensor_range == inf),
        a range sensor (if fov == 360),
        or a unidirectional sensor (if fov < 360).
        :param nodes: Dictionary of nodes; each node has attributes x and y.
        """
        self.ctx = ctx
        self.sensor_id = sensor_id
        self.type = sensor_type
        self.nodes = nodes
        self.range = sensor_range
        self.fov = fov
        self.orientation = orientation
        self.data = {}
        # Cache static node IDs and positions using x and y.
        self.node_ids = list(self.nodes.keys())
        self._positions = np.array([[self.nodes[nid].x, self.nodes[nid].y] for nid in self.node_ids])
    
    def data(self) -> Dict[str, Any]:
        return self.data
    
    def sense(self, node_id: int) -> None:
        """
        Detects nodes within the sensor range and arc.
        - If sensor_range is infinity, all nodes are included (map sensor).
        - If fov is 360, no angular filtering is applied (range sensor).
        - Otherwise, only nodes within the specified arc are returned.
        The result is stored in self.data as:
            { 'nodes': {node_id: node, ...} }
        """
        current_node = self.nodes[node_id]
        current_position = np.array([current_node.x, current_node.y]).reshape(1, 2)
        
        # --- Process static nodes ---
        diff = self._positions - current_position
        distances_sq = np.sum(diff**2, axis=1)
        if self.range == float('inf'):
            in_range_mask = np.full(distances_sq.shape, True)
        else:
            in_range_mask = distances_sq <= self.range**2
        in_range_indices = np.nonzero(in_range_mask)[0]
        
        sensed_nodes = {}
        if in_range_indices.size:
            if self.fov == 360:
                valid_indices = in_range_indices
            else:
                diff_in_range = diff[in_range_indices]
                angles = np.degrees(np.arctan2(diff_in_range[:, 1], diff_in_range[:, 0])) % 360
                orientation_norm = self.orientation % 360
                angle_diff = np.abs((angles - orientation_norm + 180) % 360 - 180)
                valid_mask = angle_diff <= (self.fov / 2)
                valid_indices = in_range_indices[valid_mask]
            sensed_nodes = {self.node_ids[i]: self.nodes[self.node_ids[i]] for i in valid_indices}
        
        self.data = {'nodes': sensed_nodes}


    def update(self, data: Dict[str, Any]) -> None:
        pass
class AgentSensor(ISensor):
    def __init__(self, ctx, sensor_id, sensor_type, agent_engine, sensor_range: float, owner: Optional[str]=None):
        """
        :param agent_engine: Typically the context's agent engine.
        :param sensor_range: Maximum detection distance for agents.
        :param owner: (Optional) The name of the agent owning this sensor.
                      If set, this agent will be skipped during sensing.
        """
        self.sensor_id = sensor_id
        self.ctx = ctx
        self.type = sensor_type
        self.agent = agent_engine
        self.range = sensor_range
        self.data = {}
        self.owner = owner
    
    def data(self) -> Dict[str, Any]:
        return self.data
    
    def sense(self, node_id: int) -> None:
        """
        Detects agents that are within the sensor range of the sensing node.
        Skips the agent whose name matches self.owner.
        The result is stored in self.data as a dictionary mapping agent name to agent.
        """
        # Get current node position.
        current_node = self.ctx.graph.graph.get_node(node_id)
        current_position = np.array([current_node.x, current_node.y]).reshape(1, 2)
        
        agents = list(self.agent.create_iter())
        sensed_agents = {}
        agent_ids = []
        agent_positions = []
        for agent in agents:
            # Skip the sensor's own agent if owner is set.
            if self.owner is not None and agent._name == self.owner:
                continue
            agent_ids.append(agent._name)
            if hasattr(agent, 'position'):
                pos = np.array(agent.position)
            else:
                node_obj = self.ctx.graph.graph.get_node(agent.current_node_id)
                pos = np.array([node_obj.x, node_obj.y])
            agent_positions.append(pos)
        
        if agent_positions:
            agent_positions = np.array(agent_positions).reshape(-1, 2)
            diff_agents = agent_positions - current_position
            distances_agents_sq = np.sum(diff_agents**2, axis=1)
            agent_in_range_mask = distances_agents_sq <= self.range**2
            in_range_agent_ids = {agent_ids[i] for i, valid in enumerate(agent_in_range_mask) if valid}
            # Build sensed_agents by iterating through agents again and picking those in range.
            for agent in agents:
                if self.owner is not None and agent._name == self.owner:
                    continue
                if agent._name in in_range_agent_ids:
                    sensed_agents[agent._name] = agent
        self.data = sensed_agents
    
    def update(self, data: Dict[str, Any]) -> None:
        pass


class SensorEngine(ISensorEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx  
        self.sensors = {}
        self.custom_sensors: Dict[str, Type[Any]] = {}
        self.custom_sensor_counter: int = 0
        
    def create_sensor(self, sensor_id, type: SensorType, **kwargs):
        if type == SensorType.NEIGHBOR:
            sensor = NeighborSensor(self.ctx, sensor_id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.MAP:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                type, 
                self.ctx.graph_engine.graph.nodes, 
                sensor_range=float('inf'),
                fov=360,
                orientation=0
            )
        elif type == SensorType.RANGE:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                type, 
                self.ctx.graph_engine.graph.nodes, 
                sensor_range=30,
                fov=360,
                orientation=0
            )
        elif type == SensorType.ARC:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                type, 
                self.ctx.graph_engine.graph.nodes, 
                sensor_range=30,
                fov=90,
                orientation=0
            )
        elif type == SensorType.AGENT:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                type, 
                self.ctx.agent, 
                sensor_range=30,
                owner=None  # Set owner when registering sensor to an agent.
            )
        else:
            raise ValueError("Invalid sensor type")
        self.sensors[sensor_id] = sensor
        return sensor
    
    def get_sensor(self, sensor_id):
        try:
            return self.sensors[sensor_id]
        except KeyError:
            raise KeyError(f"Sensor {sensor_id} not found.")
    
    def custom(self) -> Callable[[Type[_T]], Type[_T]]:
        engine = self
        def decorator(cls_type: Type[_T]) -> Type[_T]:
            original_init = cls_type.__init__
            def new_init(instance, name: str, *args, **kwargs):
                sensor_enum_name = name.upper()
                if not hasattr(SensorType, sensor_enum_name):
                    engine.custom_sensor_counter -= 1
                    custom_value = engine.custom_sensor_counter
                    setattr(SensorType, sensor_enum_name, custom_value)
                instance.custom_data = {'name': name}
                original_init(instance, *args, **kwargs)
            cls_type.__init__ = new_init
            engine.custom_sensors[cls_type.__name__] = cls_type
            return cls_type
        return decorator



    def terminate(self):
        return
    
