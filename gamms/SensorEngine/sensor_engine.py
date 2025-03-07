from gamms.typing.sensor_engine import SensorType, ISensor, ISensorEngine
from gamms.typing.context import IContext
from gamms.typing.opcodes import OpCodes
from typing import Any, Dict, Optional, Type, TypeVar, Callable
import math
import numpy as np

_T = TypeVar('_T')


class NeighborSensor(ISensor):
    def __init__(self, ctx, sensor_id, sensor_type, nodes, edges):
        self.sensor_id = sensor_id
        self.ctx = ctx
        self._type = sensor_type
        self.nodes = nodes
        self.edges = edges
        self._data = []
        self._owner = None
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self):
        return self._data

    def sense(self, node_id: int) -> None:
        outgoing_edges = []
        for edge in self.edges.values():
            if edge.source == node_id:
                outgoing_edges.append(edge)
        self._data = outgoing_edges

    def update(self, data: Dict[str, Any]) -> None:
        pass

class MapSensor(ISensor):
    def __init__(self, ctx, sensor_id, sensor_type, nodes, sensor_range: float, fov: float, orientation: float):
        """
        Acts as a map sensor (if sensor_range == inf),
        a range sensor (if fov == 2*pi),
        or a unidirectional sensor (if fov < 2*pi).
        Assumes fov and orientation are provided in radians.
        :param nodes: Dictionary of nodes; each node has attributes x and y.
        """
        self.ctx = ctx
        self.sensor_id = sensor_id
        self._type = sensor_type
        self.nodes = nodes
        self.range = sensor_range
        self.fov = fov  
        self.orientation = orientation  
        self._data = {} 
        # Cache static node IDs and positions.
        self.node_ids = list(self.nodes.keys())
        self._positions = np.array([[self.nodes[nid].x, self.nodes[nid].y] for nid in self.node_ids])
        self._owner = None
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    def sense(self, node_id: int) -> None:
        """
        Detects nodes within the sensor range and arc.
        
        The result is now stored in self._data as a dictionary with two keys:
          - 'nodes': {node_id: node, ...} for nodes that pass the sensing filter.
          - 'edges': {node_id: [edge, ...], ...} where each key is a sensed node and the value
                     is a list of edges connecting the sensing node to that node.
        """
        current_node = self.nodes[node_id]
        current_position = np.array([current_node.x, current_node.y]).reshape(1, 2)
        if self._owner is not None:
            # Fetch the owner's orientation from the agent engine.
            orientation_used = self.ctx.agent.get_agent(self._owner).orientation
        else:
            orientation_used = self.orientation % (2 * math.pi)

        diff = self._positions - current_position
        distances_sq = np.sum(diff**2, axis=1)
        if self.range == float('inf'):
            in_range_mask = np.full(distances_sq.shape, True)
        else:
            in_range_mask = distances_sq <= self.range**2
        in_range_indices = np.nonzero(in_range_mask)[0]

        sensed_nodes = {}
        if in_range_indices.size:
            if self.fov == 2 * math.pi:
                valid_indices = in_range_indices
            else:
                diff_in_range = diff[in_range_indices]
                angles = np.arctan2(diff_in_range[:, 1], diff_in_range[:, 0]) % (2 * math.pi)
                angle_diff = np.abs((angles - orientation_used + math.pi) % (2 * math.pi) - math.pi)
                valid_mask = angle_diff <= (self.fov / 2)
                valid_indices = in_range_indices[valid_mask]
            sensed_nodes = {self.node_ids[i]: self.nodes[self.node_ids[i]] for i in valid_indices}

        # Now, compute the connecting edges from the sensing node to each sensed node.
        sensed_edges = {}
        # Retrieve edges from the graph via the context's graph engine.
        graph_edges = self.ctx.graph_engine.graph.edges
        for candidate_id in sensed_nodes.keys():
            candidate_edges = []
            # Look for an edge from the sensing node to this candidate node.
            for edge in graph_edges.values():
                if edge.source == node_id and edge.target == candidate_id:
                    candidate_edges.append(edge)
            sensed_edges[candidate_id] = candidate_edges

        self._data = {'nodes': sensed_nodes, 'edges': sensed_edges}

    def update(self, data: Dict[str, Any]) -> None:
        # No dynamic updates required for this sensor.
        pass

class SensorEngine(ISensorEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx  
        self.sensors = {}
        self.custom_sensors: Dict[str, Type[Any]] = {}
        self.custom_sensor_counter: int = 0

    def create_sensor(self, sensor_id, sensor_type: SensorType, **kwargs):
        if sensor_type == SensorType.NEIGHBOR:
            sensor = NeighborSensor(
                self.ctx, sensor_id, sensor_type, 
                self.ctx.graph_engine.graph.nodes, 
                self.ctx.graph_engine.graph.edges
            )
        elif sensor_type == SensorType.MAP:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                self.ctx.graph_engine.graph.nodes, 
                sensor_range=float('inf'),
                fov=2 * math.pi,
                orientation=0
            )
        elif sensor_type == SensorType.RANGE:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                self.ctx.graph_engine.graph.nodes, 
                sensor_range=20,
                fov=2 * math.pi,
                orientation=0
            )
        elif sensor_type == SensorType.ARC:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                self.ctx.graph_engine.graph.nodes, 
                sensor_range=30,
                fov=math.radians(90),
                orientation=0
            )
        elif sensor_type == SensorType.AGENT:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                self.ctx.agent, 
                sensor_range=30,
                fov=2 * math.pi,
                owner=None  # Set owner when registering sensor to an agent.
            )
        elif sensor_type == SensorType.AGENT_ARC:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                self.ctx.agent, 
                sensor_range=30,
                fov=math.radians(90),  
                owner=None  # Set owner when registering sensor to an agent.
            )
        elif sensor_type == SensorType.AGENT_RANGE:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                self.ctx.agent, 
                sensor_range=30,
                fov=2 * math.pi,
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
