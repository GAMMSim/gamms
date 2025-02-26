from gamms.typing.sensor_engine import SensorType, ISensor, ISensorEngine
from gamms.typing.context import IContext
from gamms.typing.opcodes import OpCodes
from typing import Any, Dict, Optional, Type, TypeVar
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
        # Cache static node IDs and positions using x and y.
        self.node_ids = list(self.nodes.keys())
        self._positions = np.array([[self.nodes[nid].x, self.nodes[nid].y] for nid in self.node_ids])
    
    def data(self) -> Dict[str, Any]:
        return self.data
    
    def sense(self, node_id: int) -> None:
        """
        Detects both nodes and agents within the sensor range.
        Returns a dictionary with:
            'nodes': {node_id: node, ...}
            'agents': {agent_id: agent, ...}
        """
        current_node = self.nodes[node_id]
        current_position = np.array([current_node.x, current_node.y]).reshape(1, 2)
        
        # --- Process static nodes ---
        diff_nodes = self._positions - current_position
        distances_nodes_sq = np.sum(diff_nodes**2, axis=1)
        in_range_mask = distances_nodes_sq <= self.range**2
        in_range_node_ids = {self.node_ids[i] for i, valid in enumerate(in_range_mask) if valid}
        in_range_nodes = {nid: self.nodes[nid] for nid in in_range_node_ids}
        
        # --- Process dynamic agents ---
        agents = list(self.ctx.agent.create_iter())
        sensed_agents = {}
        if agents:
            agent_ids = []
            agent_positions = []
            for agent in agents:
                agent_ids.append(agent._name)
                if hasattr(agent, 'position'):
                    pos = np.array(agent.position)
                else:
                    # Fallback: use the agent's current node's x and y.
                    node_obj = self.ctx.graph.graph.get_node(agent.current_node_id)
                    pos = np.array([node_obj.x, node_obj.y])
                agent_positions.append(pos)
            agent_positions = np.array(agent_positions).reshape(-1, 2)
            diff_agents = agent_positions - current_position
            distances_agents_sq = np.sum(diff_agents**2, axis=1)
            agent_in_range_mask = distances_agents_sq <= self.range**2
            in_range_agent_ids = {agent_ids[i] for i, valid in enumerate(agent_in_range_mask) if valid}
            sensed_agents = {agent._name: agent for agent in agents if agent._name in in_range_agent_ids}
        
        self.data = {'nodes': in_range_nodes, 'agents': sensed_agents}
    
    def update(self, data: Dict[str, Any]) -> None:
        pass

class ArcSensor(ISensor):
    def __init__(self, ctx, sensor_id, sensor_type, nodes, sensor_range: float, fov: float, orientation: float):
        """
        :param ctx: The simulation context.
        :param sensor_id: Unique sensor identifier.
        :param sensor_type: The sensor type.
        :param nodes: Dictionary of nodes with x and y attributes.
        :param sensor_range: Maximum detection distance.
        :param fov: Field of view (arc width) in degrees.
        :param orientation: Central direction of the sensor in degrees.
        """
        self.ctx = ctx
        self.sensor_id = sensor_id
        self.type = sensor_type
        self.nodes = nodes
        self.range = sensor_range
        self.fov = fov
        self.orientation = orientation
        self.data = {}
        # Cache static node IDs and positions using node.x and node.y.
        self.node_ids = list(self.nodes.keys())
        self._positions = np.array([[self.nodes[nid].x, self.nodes[nid].y] for nid in self.node_ids])
    
    def data(self) -> Dict[str, Any]:
        return self.data
    
    def sense(self, node_id: int) -> None:
        """
        Detects nodes and agents within an arc defined by the sensor's FOV and orientation,
        and within the specified range.
        Returns a dictionary with:
            'nodes': {node_id: node, ...}
            'agents': {agent_id: agent, ...}
        """
        current_node = self.nodes[node_id]
        current_position = np.array([current_node.x, current_node.y]).reshape(1, 2)
        
        # --- Process static nodes ---
        diff = self._positions - current_position
        distances_sq = np.sum(diff**2, axis=1)
        in_range_mask = distances_sq <= self.range**2
        in_range_indices = np.nonzero(in_range_mask)[0]
        sensed_nodes = {}
        if in_range_indices.size:
            diff_in_range = diff[in_range_indices]
            angles = np.degrees(np.arctan2(diff_in_range[:, 1], diff_in_range[:, 0])) % 360
            orientation_norm = self.orientation % 360
            angle_diff = np.abs((angles - orientation_norm + 180) % 360 - 180)
            valid_mask = angle_diff <= (self.fov / 2)
            valid_indices = in_range_indices[valid_mask]
            sensed_nodes = {self.node_ids[i]: self.nodes[self.node_ids[i]] for i in valid_indices}
        
        # --- Process dynamic agents ---
        agents = list(self.ctx.agent.create_iter())
        sensed_agents = {}
        if agents:
            agent_ids = []
            agent_positions = []
            for agent in agents:
                agent_ids.append(agent._name)
                if hasattr(agent, 'position'):
                    pos = np.array(agent.position)
                else:
                    node_obj = self.ctx.graph.graph.get_node(agent.current_node_id)
                    pos = np.array([node_obj.x, node_obj.y])
                agent_positions.append(pos)
            agent_positions = np.array(agent_positions).reshape(-1, 2)
            diff_agents = agent_positions - current_position
            distances_agents_sq = np.sum(diff_agents**2, axis=1)
            agent_in_range_mask = distances_agents_sq <= self.range**2
            in_range_agent_indices = np.nonzero(agent_in_range_mask)[0]
            if in_range_agent_indices.size:
                diff_agents_in_range = diff_agents[in_range_agent_indices]
                agent_angles = np.degrees(np.arctan2(diff_agents_in_range[:, 1], diff_agents_in_range[:, 0])) % 360
                angle_diff_agents = np.abs((agent_angles - (self.orientation % 360) + 180) % 360 - 180)
                valid_agent_mask = angle_diff_agents <= (self.fov / 2)
                valid_agent_indices = in_range_agent_indices[valid_agent_mask]
                sensed_agents = {agent_ids[i]: agents[i] for i in valid_agent_indices}
        
        self.data = {'nodes': sensed_nodes, 'agents': sensed_agents}
    
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
            sensor = MapSensor(self.ctx, sensor_id, type, self.ctx.graph_engine.graph.nodes, self.ctx.graph_engine.graph.edges)
        elif type == SensorType.AGENT:
            sensor = AgentSensor(self.ctx, sensor_id, type, self.ctx.agent)
        elif type == SensorType.RANGE:
            sensor = RangeSensor(self.ctx, sensor_id, type, self.ctx.graph_engine.graph.nodes, range=30)
        elif type == SensorType.ARC:
            sensor = ArcSensor(self.ctx, sensor_id, type, self.ctx.graph_engine.graph.nodes, range=30, fov=90, orientation=0)
        else:
            raise ValueError("Invalid sensor type")
        self.sensors[sensor_id] = sensor
        return sensor
    
    def get_sensor(self, sensor_id):
        try:
            return self.sensors[sensor_id]
        except KeyError:
            raise KeyError(f"Sensor {sensor_id} not found.")
    
    def custom(self, struct: Optional[Dict[str, _T]] = None) -> None:
        engine = self
        def decorator(cls_type: Type[_T]) -> Type[_T]:
            if struct is None:
                print('No data is being tracked')
                return cls_type
            
            if not isinstance(struct, dict):
                raise TypeError("The struct must be a dictionary.")
            for key in struct:
                if not isinstance(key, str):
                    raise TypeError("All keys in struct must be strings.")
                if key == "name":
                    raise TypeError("'name' is a reserved key for custom sensors.")
            
            setattr(cls_type, '__custom_struct__', struct)
            engine.custom_sensors[cls_type.__name__] = cls_type

            original_init = cls_type.__init__
            def new_init(instance, name: str, *args, **kwargs):
                # Convert the provided name to uppercase to use as the enum member name.
                sensor_enum_name = name.upper()
                if not hasattr(SensorType, sensor_enum_name):
                    # Assign a unique negative value and update the SensorType enum.
                    engine.custom_sensor_counter -= 1
                    custom_value = engine.custom_sensor_counter
    
                    setattr(SensorType, sensor_enum_name, custom_value)
                instance.custom_data = {'name': name}
                for key in struct:
                    instance.custom_data.setdefault(key, None)

                # Call the original __init__ (without the 'name' argument).
                original_init(instance, *args, **kwargs)
            cls_type.__init__ = new_init

            return cls_type
        return decorator


    def terminate(self):
        return
    
