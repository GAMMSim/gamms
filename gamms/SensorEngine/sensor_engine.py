import gamms.typing
from gamms.typing import(
    IContext,
    ISensor,
    ISensorEngine,
    SensorType,
    OpCodes,
)

from typing import Any, Dict, Optional, Type, TypeVar, Callable, Tuple
from aenum import extend_enum
import math
import numpy as np

_T = TypeVar('_T')


class NeighborSensor(ISensor):
    def __init__(self, ctx, sensor_id, sensor_type):
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
    
    def set_owner(self, owner: str) -> None:
        self._owner = owner

    def sense(self, node_id: int) -> None:
        nearest_neighbors = self.ctx.memory.query_store(
            name="edges",
            sql = f"""
                SELECT 
                    CASE 
                        WHEN source = {node_id} THEN target
                        WHEN target = {node_id} THEN source
                    END AS neighbor_id
                FROM edges
                WHERE source = {node_id} OR target = {node_id}
                """,
            params = None
        )
        data = set([item["neighbor_id"] for item in nearest_neighbors])         
        self._data = list(data)

    def update(self, data: Dict[str, Any]) -> None:
        pass

class MapSensor(ISensor):
    def __init__(self, ctx, sensor_id, sensor_type, sensor_range: float, fov: float, orientation: Tuple[float, float] = (1.0, 0.0)):
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
        self._data = {}
        self._owner = None
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> Dict[str, Any]:
        return self._data
    
    def set_owner(self, owner: str) -> None:
        self._owner = owner

    def sense(self, node_id: int) -> None:
        """
        Detects nodes within the sensor range and arc.
        
        The result is stored in self._data as a dictionary with two keys:
          - 'nodes': {node_id: {'id': id, 'x': x, 'y': y}, ...} for nodes that pass the sensing filter.
          - 'edges': List of edges visible from all sensed nodes.
        """
        # Get current node position
        current_node_data = self.ctx.memory.query_store(
            name="nodes",
            sql="SELECT id, x, y FROM nodes WHERE id = ?",
            params=[node_id]
        )
        
        if not current_node_data:
            self._data = {'nodes': {}, 'edges': []}
            return
            
        current_node = current_node_data[0]
        current_x, current_y = current_node['x'], current_node['y']
        
        # Determine orientation to use
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

        # Query nodes based on range
        if self.range == float('inf'):
            # Get all nodes for map sensor
            nodes_in_range = self.ctx.memory.query_store(
                name="nodes",
                sql="SELECT id, x, y FROM nodes",
                params=None
            )
        else:
            # Use spatial query for range-limited sensors
            # SQLite doesn't have built-in spatial functions, so we'll get all nodes
            #@ Rohan: This is a workaround for range-limited sensors? maybe we can optimize this later.
            # For now, we will use a simple distance calculation.
            #SpatialLite extension could be used for better performance.
            nodes_in_range = self.ctx.memory.query_store(
                name="nodes",
                sql="""
                SELECT id, x, y,
                       ((x - ?) * (x - ?) + (y - ?) * (y - ?)) as distance_sq
                FROM nodes 
                WHERE ((x - ?) * (x - ?) + (y - ?) * (y - ?)) <= ?
                """,
                params=[current_x, current_x, current_y, current_y, 
                       current_x, current_x, current_y, current_y, 
                       self.range**2]
            )

        sensed_nodes = {}
        
        # Apply field of view filtering if needed
        if self.fov == 2 * math.pi or orientation_used == (0.0, 0.0):
            # No angular filtering needed
            for node in nodes_in_range:
                sensed_nodes[node['id']] = {
                    'id': node['id'], 
                    'x': node['x'], 
                    'y': node['y']
                }
        else:
            # Apply field of view filtering
            orientation_angle = np.arctan2(orientation_used[1], orientation_used[0]) % (2 * math.pi)
            
            for node in nodes_in_range:
                if node['id'] == node_id:  # Always include current node
                    sensed_nodes[node['id']] = {
                        'id': node['id'], 
                        'x': node['x'], 
                        'y': node['y']
                    }
                    continue
                    
                # Calculate angle to this node
                dx = node['x'] - current_x
                dy = node['y'] - current_y
                node_angle = np.arctan2(dy, dx) % (2 * math.pi)
                
                # Check if within field of view
                angle_diff = abs((node_angle - orientation_angle + math.pi) % (2 * math.pi) - math.pi)
                if angle_diff <= (self.fov / 2):
                    sensed_nodes[node['id']] = {
                        'id': node['id'], 
                        'x': node['x'], 
                        'y': node['y']
                    }

        # Always include current node
        sensed_nodes[node_id] = {
            'id': current_node['id'], 
            'x': current_node['x'], 
            'y': current_node['y']
        }

        # Query edges that connect any of the sensed nodes
        sensed_edges = []
        if len(sensed_nodes) > 1:  # Only query edges if we have multiple nodes
            sensed_node_ids = list(sensed_nodes.keys())
            placeholders = ','.join('?' * len(sensed_node_ids))
            
            edges_data = self.ctx.memory.query_store(
                name="edges",
                sql=f"""
                SELECT id, source, target, length
                FROM edges 
                WHERE source IN ({placeholders}) AND target IN ({placeholders})
                """,
                params=sensed_node_ids + sensed_node_ids
            )
            
            sensed_edges = [
                {
                    'id': edge['id'],
                    'source': edge['source'],
                    'target': edge['target'],
                    'length': edge['length']
                }
                for edge in edges_data
            ]

        self._data = {'nodes': sensed_nodes, 'edges': sensed_edges}

    def update(self, data: Dict[str, Any]) -> None:
        # No dynamic updates required for this sensor.
        pass
class AgentSensor(ISensor):
    def __init__(
        self, 
        ctx, 
        sensor_id, 
        sensor_type, 
        sensor_range: float, 
        fov: float = 2 * math.pi, 
        orientation: Tuple[float, float] = (1.0, 0.0), 
        owner: Optional[str] = None
    ):
        """
        Detects other agents within a specified range and field of view.
        :param sensor_range: Maximum detection distance for agents.
        :param fov: Field of view in radians. Use 2*pi for no angular filtering.
        :param orientation: Default orientation tuple (cos, sin) if no owner is set.
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
        self._data = {}
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    def set_owner(self, owner: str) -> None:
        self._owner = owner
        
    def sense(self, node_id: int) -> None:
        """
        Detects agents within the sensor range of the sensing node.
        Skips the agent whose name matches self._owner.
        
        The result is stored in self._data as a dictionary mapping agent names to their current node IDs.
        """
        # Get current node position
        current_node_data = self.ctx.memory.query_store(
            name="nodes",
            sql="SELECT id, x, y FROM nodes WHERE id = ?",
            params=[node_id]
        )
        
        if not current_node_data:
            self._data = {}
            return
            
        current_node = current_node_data[0]
        current_x, current_y = current_node['x'], current_node['y']

        # Get all agents and their positions
        agents = list(self.ctx.agent.create_iter())
        sensed_agents = {}

        # Determine orientation to use
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

        # Check each agent
        for agent in agents:
            # Skip the owner agent
            if self._owner is not None and agent.name == self._owner:
                continue

            # Get agent's position
            agent_node_data = self.ctx.memory.query_store(
                name="nodes",
                sql="SELECT id, x, y FROM nodes WHERE id = ?",
                params=[agent.current_node_id]
            )
            
            if not agent_node_data:
                continue
                
            agent_node = agent_node_data[0]
            agent_x, agent_y = agent_node['x'], agent_node['y']

            # Calculate distance
            distance_sq = (agent_x - current_x)**2 + (agent_y - current_y)**2
            
            # Check if within range
            if self.range != float('inf') and distance_sq > self.range**2:
                continue

            # Check field of view if applicable
            if self.fov != 2 * math.pi and orientation_used != (0.0, 0.0):
                # Calculate angle to agent
                dx = agent_x - current_x
                dy = agent_y - current_y
                
                if dx == 0 and dy == 0:  # Same position
                    sensed_agents[agent.name] = agent.current_node_id
                    continue
                
                agent_angle = np.arctan2(dy, dx) % (2 * math.pi)
                orientation_angle = np.arctan2(orientation_used[1], orientation_used[0]) % (2 * math.pi)
                
                # Check if within field of view
                angle_diff = abs((agent_angle - orientation_angle + math.pi) % (2 * math.pi) - math.pi)
                if angle_diff <= (self.fov / 2):
                    sensed_agents[agent.name] = agent.current_node_id
            else:
                # No angular filtering, agent is within range
                sensed_agents[agent.name] = agent.current_node_id

        self._data = sensed_agents

    def update(self, data: Dict[str, Any]) -> None:
        # No dynamic updates required for this sensor.
        pass

class SensorEngine(ISensorEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx  
        self.sensors = {}

    def create_sensor(self, sensor_id, sensor_type: SensorType, **kwargs):
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
                sensor_range=kwargs.get('sensor_range', 30),
                fov=(2 * math.pi),
            )
        elif sensor_type == SensorType.ARC:
            sensor = MapSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=kwargs.get('sensor_range', 30),
                fov=kwargs.get('fov', 2 * math.pi),
            )
        elif sensor_type == SensorType.AGENT:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=float('inf'),
                fov=kwargs.get('fov', 2 * math.pi),
            )
        elif sensor_type == SensorType.AGENT_ARC:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=kwargs.get('sensor_range', 30),
                fov=kwargs.get('fov', math.radians(90)), 
            )
        elif sensor_type == SensorType.AGENT_RANGE:
            sensor = AgentSensor(
                self.ctx, 
                sensor_id, 
                sensor_type, 
                sensor_range=kwargs.get('sensor_range', 30),
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

    def get_sensor(self, sensor_id):
        try:
            return self.sensors[sensor_id]
        except KeyError:
            raise KeyError(f"Sensor {sensor_id} not found.")

    def custom(self, name: str) -> Callable[[Type[_T]], Type[_T]]:
        if hasattr(SensorType, name):
            raise ValueError(f"SensorType {name} already exists.")
        extend_enum(SensorType, name, len(SensorType))
        val = getattr(SensorType, name)
        def decorator(cls_type: Type[_T]) -> Type[_T]:
            cls_type.type = property(lambda obj: val)
            return cls_type
        return decorator

    def terminate(self):
        return
