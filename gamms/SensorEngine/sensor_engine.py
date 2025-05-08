from gamms.typing import(
    IContext,
    ISensor,
    ISensorEngine,
    SensorType,
    Node,
    OSMEdge,
)

from typing import Any, Dict, Optional, Callable, Tuple, List, Union, cast
from aenum import extend_enum
import math
import numpy as np

class NeighborSensor(ISensor):
    def __init__(self, ctx: IContext, sensor_id: str, sensor_type: SensorType):
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._type = sensor_type
        self._data = []
        self._owner = None
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self):
        return self._data
    
    def set_owner(self, owner: Union[str, None]) -> None:
        self._owner = owner

    def sense(self, node_id: int) -> None:
        nearest_neighbors = {node_id,}
        for edge_id in self.ctx.graph.graph.get_edges():
            edge = self.ctx.graph.graph.get_edge(edge_id)
            if edge.source == node_id:
                nearest_neighbors.add(edge.target)
                        
        self._data = list(nearest_neighbors)

    def update(self, data: Dict[str, Any]) -> None:
        pass

class MapSensor(ISensor):
    def __init__(self, ctx: IContext, sensor_id: str, sensor_type: SensorType, sensor_range: float, fov: float, orientation: Tuple[float, float] = (1.0, 0.0)):
        """
        Acts as a map sensor (if sensor_range == inf),
        a range sensor (if fov == 2*pi),
        or a unidirectional sensor (if fov < 2*pi).
        Assumes fov and orientation are provided in radians.
        """
        self.ctx = ctx
        self._sensor_id = sensor_id
        self._type = sensor_type
        self.range = sensor_range
        self.fov = fov  
        norm = math.sqrt(orientation[0]**2 + orientation[1]**2)
        self.orientation = (orientation[0] / norm, orientation[1] / norm)
        self._data: Dict[str, Union[Dict[int, Node], List[OSMEdge]]] = {}
        # Cache static node IDs and positions.
        self.nodes = cast(Dict[int, Node], self.ctx.graph.graph.nodes)
        self.node_ids: List[int] = list(self.nodes.keys())
        self._positions = np.array([[self.nodes[nid].x, self.nodes[nid].y] for nid in self.node_ids], dtype=np.float32)
        self._owner = None
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> Dict[str, Union[Dict[int, Node],List[OSMEdge]]]:
        return self._data
    
    def set_owner(self, owner: Union[str, None]) -> None:
        self._owner = owner

    def sense(self, node_id: int) -> None:
        """
        Detects nodes within the sensor range and arc.
        
        The result is now stored in self._data as a dictionary with two keys:
          - 'nodes': {node_id: node, ...} for nodes that pass the sensing filter.
          - 'edges': List of edges visible from all sensed nodes.
        """
        current_node = self.nodes[node_id]
        current_position = np.array([current_node.x, current_node.y]).reshape(1, 2)
        if self._owner is not None:
            # Fetch the owner's orientation from the agent engine.
            orientation_used = self.ctx.agent.get_agent(self._owner).orientation
            # Complex multiplication to rotate the orientation vector.
            orientation_used = (
                self.orientation[0]*orientation_used[0] - self.orientation[1]*orientation_used[1], 
                self.orientation[0]*orientation_used[1] + self.orientation[1]*orientation_used[0]
            )
        else:
            orientation_used = self.orientation

        diff = self._positions - current_position
        distances_sq = np.sum(diff**2, axis=1)
        if self.range == float('inf'):
            in_range_mask = np.full(distances_sq.shape, True)
        else:
            in_range_mask = distances_sq <= self.range**2
        in_range_indices = np.nonzero(in_range_mask)[0]

        sensed_nodes: Dict[int, Node] = {}
        if in_range_indices.size:
            if self.fov == 2 * math.pi or orientation_used == (0.0, 0.0):
                valid_indices = in_range_indices
            else:
                orientation_used = np.atan2(orientation_used[1], orientation_used[0]) % (2 * math.pi)
                diff_in_range = diff[in_range_indices]
                angles = np.arctan2(diff_in_range[:, 1], diff_in_range[:, 0]) % (2 * math.pi)
                angle_diff = np.abs((angles - orientation_used + math.pi) % (2 * math.pi) - math.pi)
                valid_mask = angle_diff <= (self.fov / 2)
                valid_indices = in_range_indices[valid_mask]
            sensed_nodes = {self.node_ids[i]: self.nodes[self.node_ids[i]] for i in valid_indices}
        
        sensed_nodes[node_id] = current_node

        # Now, compute the connecting edges from the sensing node to each sensed node.
        sensed_edges: List[OSMEdge] = []
        # Retrieve edges from the graph via the context's graph engine.
        graph_edges = cast(Dict[int, OSMEdge], self.ctx.graph.graph.edges)
        for edge in graph_edges.values():
            if edge.source in sensed_nodes and edge.target in sensed_nodes:
                sensed_edges.append(edge)

        self._data = {'nodes': sensed_nodes, 'edges': sensed_edges}

    def update(self, data: Dict[str, Any]) -> None:
        # No dynamic updates required for this sensor.
        pass

class AgentSensor(ISensor):
    def __init__(
        self, 
        ctx: IContext, 
        sensor_id: str, 
        sensor_type: SensorType, 
        sensor_range: float, 
        fov: float = 2 * math.pi, 
        orientation: Tuple[float, float] = (1.0, 0.0), 
        owner: Optional[str] = None
    ):
        """
        Detects other agents within a specified range and field of view.
        :param agent_engine: Typically the context's agent engine.
        :param sensor_range: Maximum detection distance for agents.
        :param fov: Field of view in radians. Use 2*pi for no angular filtering.
        :param orientation: Default orientation (in radians) if no owner is set.
        :param owner: (Optional) The name of the agent owning this sensor.
                      This agent will be skipped during sensing.
        """
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._type = sensor_type
        self.range = sensor_range
        self.fov = fov              
        self.orientation = orientation  
        self._owner = owner
        self._data: Dict[str, int] = {}
    

    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> Dict[str, int]:
        return self._data

    def set_owner(self, owner: Union[str, None]) -> None:
        self._owner = owner
        
    def sense(self, node_id: int) -> None:
        """
        Detects agents within the sensor range of the sensing node.
        Skips the agent whose name matches self._owner.
        In addition to a range check, if self.fov != 2*pi, only agents within (fov/2) radians
        of the chosen orientation are included.
        The chosen orientation is determined as follows:
         - If self._owner is set, fetch the owner's orientation from the agent engine.
         - Otherwise, use self.orientation.
        The result is stored in self._data as a dictionary mapping agent names to agent objects.
        """
        # Get current node position as sensing origin.
        current_node = self.ctx.graph.graph.get_node(node_id)
        current_position = np.array([current_node.x, current_node.y]).reshape(1, 2)

        agents = list(self.ctx.agent.create_iter())
        sensed_agents = {}
        agent_ids: List[str] = []
        agent_positions = []

        # Collect positions and ids for all agents except the owner.
        for agent in agents:
            if self._owner is not None and agent.name == self._owner:
                continue
            agent_ids.append(agent.name)
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
            in_range_mask = distances_agents_sq <= self.range**2
            in_range_indices = np.nonzero(in_range_mask)[0]

            if self._owner is not None:
                # Fetch the owner's orientation from the agent engine.
                orientation_used = self.ctx.agent.get_agent(self._owner).orientation
                # Complex multiplication to rotate the orientation vector.
                orientation_used = (
                    self.orientation[0]*orientation_used[0] - self.orientation[1]*orientation_used[1], 
                    self.orientation[0]*orientation_used[1] + self.orientation[1]*orientation_used[0]
                )
            else:
                orientation_used = self.orientation

            if self.fov == 2 * math.pi or orientation_used == (0.0, 0.0):
                valid_indices = in_range_indices
            else:
                orientation_used = np.arctan2(orientation_used[1], orientation_used[0]) % (2 * math.pi)
                diff_in_range = diff_agents[in_range_indices]
                angles = np.arctan2(diff_in_range[:, 1], diff_in_range[:, 0]) % (2 * math.pi)
                angle_diff = np.abs((angles - orientation_used + math.pi) % (2 * math.pi) - math.pi)
                valid_mask = angle_diff <= (self.fov / 2)
                valid_indices = in_range_indices[valid_mask]

            in_range_agent_ids = {agent_ids[i] for i in valid_indices}
            for agent in agents:
                if self._owner is not None and agent.name == self._owner:
                    continue
                if agent.name in in_range_agent_ids:
                    sensed_agents[agent.name] = agent.current_node_id

        self._data = sensed_agents

    def update(self, data: Dict[str, Any]) -> None:
        # No dynamic updates required for this sensor.
        pass

class SensorEngine(ISensorEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx  
        self.sensors: Dict[str, ISensor] = {}

    def create_sensor(self, sensor_id: str, sensor_type: SensorType, **kwargs: Dict[str, Any]) -> ISensor:
        if sensor_type == SensorType.NEIGHBOR:
            sensor = NeighborSensor(
                self.ctx, sensor_id, sensor_type, 
            )
        elif sensor_type == SensorType.MAP:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=float('inf'),
                fov=2 * math.pi,
            )
        elif sensor_type == SensorType.RANGE:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=(2 * math.pi),
            )
        elif sensor_type == SensorType.ARC:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
            )
        elif sensor_type == SensorType.AGENT:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=float('inf'),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
            )
        elif sensor_type == SensorType.AGENT_ARC:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)), 
            )
        elif sensor_type == SensorType.AGENT_RANGE:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=2 * math.pi,
            )
        else:
            raise ValueError("Invalid sensor type")
        self.sensors[sensor_id] = sensor
        return sensor
    
    def add_sensor(self, sensor: ISensor) -> None:
        sensor_id = sensor.sensor_id
        if sensor_id in self.sensors:
            raise ValueError(f"Sensor {sensor_id} already exists.")
        self.sensors[sensor_id] = sensor

    def get_sensor(self, sensor_id: str) -> ISensor:
        try:
            return self.sensors[sensor_id]
        except KeyError:
            raise KeyError(f"Sensor {sensor_id} not found.")

    def custom(self, name: str) -> Callable[[ISensor], ISensor]:
        if hasattr(SensorType, name):
            raise ValueError(f"SensorType {name} already exists.")
        extend_enum(SensorType, name, len(SensorType))
        val = getattr(SensorType, name)
        def decorator(cls_type: ISensor) -> ISensor:
            cls_type.type = property(lambda obj: val)
            return cls_type
        return decorator

    def terminate(self):
        return
