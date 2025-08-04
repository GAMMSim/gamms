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
        for nid in self.ctx.graph.graph.get_neighbors(node_id):
            nearest_neighbors.add(nid)

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
        current_node = self.ctx.graph.graph.get_node(node_id)
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
        
        if self.range == float('inf'):
            edge_iter = self.ctx.graph.graph.get_edges()
        else:
            edge_iter = self.ctx.graph.graph.get_edges(d=self.range, x=current_node.x, y=current_node.y)


        sensed_nodes: Dict[int, Node] = {}
        sensed_edges: List[OSMEdge] = []

        for edge_id in edge_iter:
            edge = self.ctx.graph.graph.get_edge(edge_id)
            source = self.ctx.graph.graph.get_node(edge.source)
            target = self.ctx.graph.graph.get_node(edge.target)
            sbool = (source.x - current_node.x)**2 + (source.y - current_node.y)**2 <= self.range**2
            tbool = (target.x - current_node.x)**2 + (target.y - current_node.y)**2 <= self.range**2
            if not (self.fov == 2 * math.pi or orientation_used == (0.0, 0.0)):
                angle = math.atan2(source.y - current_node.y, source.x - current_node.x) - math.atan2(orientation_used[1], orientation_used[0]) + math.pi
                angle = angle % (2 * math.pi)
                angle = angle - math.pi
                sbool &= (
                    abs(angle) <= self.fov / 2
                ) or (source.id == node_id)
                angle = math.atan2(target.y - current_node.y, target.x - current_node.x) - math.atan2(orientation_used[1], orientation_used[0]) + math.pi
                angle = angle % (2 * math.pi)
                angle = angle - math.pi
                tbool &= (
                    abs(angle) <= self.fov / 2
                ) or (target.id == node_id)
            if sbool:
                sensed_nodes[source.id] = source
            if tbool:
                sensed_nodes[target.id] = target
            if sbool and tbool:
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

        sensed_agents = {}

        # Collect positions and ids for all agents except the owner.
        for agent in self.ctx.agent.create_iter():
            if agent.name == self._owner:
                continue
            
            agent_node = self.ctx.graph.graph.get_node(agent.current_node_id)
            distance = (agent_node.x - current_node.x)**2 + (agent_node.y - current_node.y)**2
            
            if distance <= self.range**2:
                if self.fov == 2 * math.pi or orientation_used == (0.0, 0.0):
                    sensed_agents[agent.name] = agent.current_node_id
                else:
                    angle = math.atan2(agent_node.y - current_node.y, agent_node.x - current_node.x) - math.atan2(orientation_used[1], orientation_used[0]) + math.pi
                    angle = angle % (2 * math.pi)
                    angle = angle - math.pi
                    if abs(angle) <= self.fov / 2 or agent.current_node_id == node_id:
                        sensed_agents[agent.name] = agent.current_node_id

        self._data = sensed_agents

    def update(self, data: Dict[str, Any]) -> None:
        # No dynamic updates required for this sensor.
        pass
from gamms.typing import (
    IContext,
    ISensor,
    SensorType,
    Node,
    OSMEdge,
    AgentType,
)
from typing import Dict, Any, List, Tuple, Union, cast
import numpy as np
import math


class AerialMovementSensor(ISensor):
    def __init__(self, ctx: IContext, sensor_id: str, sensor_type: SensorType):
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._type = sensor_type
        self._data: List[Tuple[float, float, float]] = []
        self._owner = None
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> List[Tuple[float, float, float]]:
        return self._data
    
    def set_owner(self, owner: Union[str, None]) -> None:
        self._owner = owner

    def sense(self, node_id: int, **kwargs) -> None:
        """
        Calculate possible movement positions in a circle around current position.
        
        Args:
            node_id: Current node (may not be used if drone is airborne)
            **kwargs: 
                pos: Current (x, y, z) position
                speed: Movement speed (default 30)
        """
        # Get position from kwargs first, then try to get from owner agent
        pos = kwargs.get('pos', None)
        speed = kwargs.get('speed', 30)  # Default speed if not provided
        
        # If no position in kwargs and we have an owner, get position from agent
        if pos is None and self._owner is not None:
            try:
                agent = self.ctx.agent.get_agent(self._owner)
                # Check if it's an aerial agent
                if hasattr(agent, 'type') and agent.type == AgentType.AERIAL:
                    pos = agent.position
                    # Get speed from agent if available
                    if hasattr(agent, '_speed'):
                        speed = agent._speed
                else:
                    # For ground agents, use node position
                    node = self.ctx.graph.graph.get_node(agent.current_node_id)
                    pos = (node.x, node.y, 0.0)
            except (KeyError, AttributeError):
                # Fallback to node position if agent not found or doesn't have position
                if node_id is not None:
                    node = self.ctx.graph.graph.get_node(node_id)
                    pos = (node.x, node.y, 0.0)
        
        # If still no position, fallback to node
        if pos is None and node_id is not None:
            node = self.ctx.graph.graph.get_node(node_id)
            pos = (node.x, node.y, 0.0)
        
        possible_positions = []
        if pos is not None:
            x, y, z = pos
            # Generate 36 positions (every 10 degrees) at the given speed
            for angle in np.linspace(0, 2 * np.pi, num=36, endpoint=False):
                new_x = x + speed * np.cos(angle)
                new_y = y + speed * np.sin(angle)
                possible_positions.append((new_x, new_y, z))  # Maintain altitude
        
        self._data = possible_positions

    def update(self, data: Dict[str, Any]) -> None:
        pass


class AerialSensor(ISensor):
    def __init__(self, ctx: IContext, sensor_id: str, sensor_type: SensorType, 
                 sensor_range: float, fov: float = math.pi/3):  # Default 60° FOV
        """
        Downward-facing conic sensor for aerial agents.
        
        Args:
            sensor_range: Maximum slant distance from drone to detected point
            fov: Field of view angle in radians (half-angle of cone)
        """
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._type = sensor_type
        self._data: Dict[str, Union[Dict[int, Node], List[OSMEdge]]] = {}
        self._owner = None
        self.range = sensor_range
        self.fov = min(fov, math.pi * 0.9)  # Cap at ~162° to avoid backward vision
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> Dict[str, Union[Dict[int, Node], List[OSMEdge]]]:
        return self._data
    
    def set_owner(self, owner: Union[str, None]) -> None:
        self._owner = owner

    def sense(self, node_id: int, **kwargs) -> None:
        """
        Detect nodes within the conic field of view from the drone's position.
        
        Args:
            node_id: Current node (may not be used if drone is airborne)
            **kwargs:
                pos: Current (x, y, z) position of the drone
        """
        # Get position from kwargs first, then try to get from owner agent
        pos = kwargs.get('pos', None)
        
        # If no position in kwargs and we have an owner, get position from agent
        if pos is None and self._owner is not None:
            try:
                agent = self.ctx.agent.get_agent(self._owner)
                # Check if it's an aerial agent
                if hasattr(agent, 'type') and agent.type == AgentType.AERIAL:
                    pos = agent.position
                else:
                    # For ground agents, use node position with z=0
                    node = self.ctx.graph.graph.get_node(agent.current_node_id)
                    pos = (node.x, node.y, 0.0)
            except (KeyError, AttributeError):
                # Fallback to node position if agent not found
                if node_id is not None:
                    node = self.ctx.graph.graph.get_node(node_id)
                    pos = (node.x, node.y, 0.0)
        
        # If still no position, fallback to node
        if pos is None and node_id is not None:
            node = self.ctx.graph.graph.get_node(node_id)
            pos = (node.x, node.y, 0.0)
        
        # If no position provided or on ground (z=0), return empty
        if pos is None or pos[2] <= 0:
            self._data = {'nodes': {}, 'edges': []}
            return
        
        x, y, height = pos
        
        # Calculate the radius of visibility on the ground
        # Based on cone geometry and sensor range constraints
        half_angle = self.fov / 2
        
        # Cone radius at ground level
        cone_radius = height * math.tan(half_angle)
        
        # Maximum ground radius based on sensor range
        # Using Pythagorean theorem: ground_radius² + height² = sensor_range²
        max_ground_radius_sq = max(0, self.range**2 - height**2)
        max_ground_radius = math.sqrt(max_ground_radius_sq)
        
        # Effective visible radius is the minimum of the two
        visible_radius = min(cone_radius, max_ground_radius)
        
        # Get all nodes from the graph
        nodes = cast(Dict[int, Node], self.ctx.graph.graph.nodes)
        sensed_nodes: Dict[int, Node] = {}
        
        # Check each node if it's within the visible circle on the ground
        for node_id_iter, node in nodes.items():
            # Calculate distance from drone's ground position to node
            dx = node.x - x
            dy = node.y - y
            ground_distance = math.sqrt(dx**2 + dy**2)
            
            # Check if within visible radius
            if ground_distance <= visible_radius:
                # Also verify it's within sensor range (hypotenuse check)
                slant_distance = math.sqrt(ground_distance**2 + height**2)
                if slant_distance <= self.range:
                    sensed_nodes[node_id_iter] = node
        
        # Get edges connecting sensed nodes
        sensed_edges: List[OSMEdge] = []
        if len(sensed_nodes) > 1:
            graph_edges = cast(Dict[int, OSMEdge], self.ctx.graph.graph.edges)
            for edge in graph_edges.values():
                if edge.source in sensed_nodes and edge.target in sensed_nodes:
                    sensed_edges.append(edge)
        
        self._data = {'nodes': sensed_nodes, 'edges': sensed_edges}

    def update(self, data: Dict[str, Any]) -> None:
        pass


class AerialAgentSensor(ISensor):
    def __init__(
        self, 
        ctx: IContext, 
        sensor_id: str, 
        sensor_type: SensorType, 
        sensor_range: float, 
        fov: float = 2 * math.pi, 
        quat: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    ):
        """
        Detects other aerial agents within a specified 3D range and field of view.
        Similar to AgentSensor but works in 3D space for aerial agents.
        
        Args:
            sensor_range: Maximum detection distance for agents
            fov: Field of view in radians. Use 2*pi for no angular filtering
            quat: Default quaternion (w, x, y, z) if no owner is set
        """
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._type = sensor_type
        self.range = sensor_range
        self.fov = fov              
        self.quat = quat  
        self._owner = None
        self._data: Dict[str, Tuple[float, float, float]] = {}
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return self._type

    @property
    def data(self) -> Dict[str, Tuple[float, float, float]]:
        return self._data

    def set_owner(self, owner: Union[str, None]) -> None:
        self._owner = owner
    
    def _quat_to_orientation(self, quat: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """
        Convert quaternion (w, x, y, z) to orientation (sin, cos).
        This extracts the yaw rotation from the quaternion for horizontal FOV calculations.
        """
        w, x, y, z = quat
        # Calculate yaw angle from quaternion
        sin_theta = 2 * (w * z + x * y)
        cos_theta = 1 - 2 * (y**2 + z**2)
        return (sin_theta, cos_theta)
        
    def sense(self, node_id: int, **kwargs) -> None:
        """
        Detects agents within the sensor range in 3D space.
        Returns agent positions instead of node IDs for aerial agents.
        """
        # Get sensing position
        pos = kwargs.get('pos', None)
        
        # If no position in kwargs and we have an owner, get position from agent
        if pos is None and self._owner is not None:
            try:
                agent = self.ctx.agent.get_agent(self._owner)
                if hasattr(agent, 'type') and agent.type == AgentType.AERIAL:
                    pos = agent.position
                else:
                    node = self.ctx.graph.graph.get_node(agent.current_node_id)
                    pos = (node.x, node.y, 0.0)
            except (KeyError, AttributeError):
                if node_id is not None:
                    node = self.ctx.graph.graph.get_node(node_id)
                    pos = (node.x, node.y, 0.0)
        
        # Fallback to node position
        if pos is None and node_id is not None:
            node = self.ctx.graph.graph.get_node(node_id)
            pos = (node.x, node.y, 0.0)
        
        if pos is None:
            self._data = {}
            return
        
        current_x, current_y, current_z = pos

        # Get orientation for FOV calculations
        if self._owner is not None:
            try:
                owner_agent = self.ctx.agent.get_agent(self._owner)
                if hasattr(owner_agent, 'quat'):
                    owner_quat = owner_agent.quat
                    orientation_used = self._quat_to_orientation(owner_quat)
                    # Apply sensor's quaternion rotation to owner's orientation
                    sensor_orientation = self._quat_to_orientation(self.quat)
                    # Complex multiplication to combine orientations
                    orientation_used = (
                        sensor_orientation[0]*orientation_used[0] - sensor_orientation[1]*orientation_used[1], 
                        sensor_orientation[0]*orientation_used[1] + sensor_orientation[1]*orientation_used[0]
                    )
                else:
                    orientation_used = self._quat_to_orientation(self.quat)
            except (KeyError, AttributeError):
                orientation_used = self._quat_to_orientation(self.quat)
        else:
            orientation_used = self._quat_to_orientation(self.quat)

        sensed_agents = {}

        # Check all agents except the owner
        for agent in self.ctx.agent.create_iter():
            if agent.name == self._owner:
                continue
            
            # Get agent position
            if hasattr(agent, 'type') and agent.type == AgentType.AERIAL:
                agent_pos = agent.position
            else:
                agent_node = self.ctx.graph.graph.get_node(agent.current_node_id)
                agent_pos = (agent_node.x, agent_node.y, 0.0)
            
            # Calculate 3D distance
            dx = agent_pos[0] - current_x
            dy = agent_pos[1] - current_y
            dz = agent_pos[2] - current_z
            distance_3d = math.sqrt(dx**2 + dy**2 + dz**2)
            
            if distance_3d <= self.range:
                # Check FOV (only considering horizontal angle for now)
                if self.fov == 2 * math.pi or orientation_used == (0.0, 0.0):
                    sensed_agents[agent.name] = agent_pos
                else:
                    # Calculate horizontal angle
                    if dx != 0 or dy != 0:  # Avoid division by zero
                        angle = math.atan2(dy, dx) - math.atan2(orientation_used[1], orientation_used[0]) + math.pi
                        angle = angle % (2 * math.pi) - math.pi
                        if abs(angle) <= self.fov / 2:
                            sensed_agents[agent.name] = agent_pos
                    else:
                        # Agent is at same horizontal position
                        sensed_agents[agent.name] = agent_pos

        self._data = sensed_agents

    def update(self, data: Dict[str, Any]) -> None:
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
        elif sensor_type == SensorType.AERIAL_MOVEMENT:
            sensor = AerialMovementSensor(
                self.ctx, sensor_id, sensor_type
            )
        elif sensor_type == SensorType.AERIAL:
            sensor = AerialSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', 100.0)),
                fov=cast(float, kwargs.get('fov', math.pi/3))  # Default 60° FOV
            )
        elif sensor_type == SensorType.AERIAL_AGENT:
            sensor = AerialAgentSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', 100.0)),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
                quat=kwargs.get('quat', (1.0, 0.0, 0.0, 0.0))
            )
        else:
            raise ValueError("Invalid sensor type")
        self.add_sensor(sensor)
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
