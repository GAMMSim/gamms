from gamms.typing import(
    IContext,
    ISensor,
    ISensorEngine,
    SensorType,
    Node,
    OSMEdge,
    AgentType,
    IAerialAgent
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

def multiply_quaternions(q1: Tuple[float, float, float, float], q2: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    )

def quaternion_to_direction(quat: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
    w, x, y, z = quat
    # Convert quaternion to direction vector (assuming forward is along the x-axis)
    return (
        1 - 2*(y**2 + z**2),
        2*(x*y + w*z),
        2*(x*z - w*y)
    )

class AerialSensor(ISensor):
    def __init__(
        self,
        ctx: IContext,
        sensor_id: str,
        sensor_range: float,
        fov: float = math.pi / 3,
        quat: Tuple[float, float, float, float] = (math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0)
    ):  # Default 60° FOV
        """
        Downward-facing conic sensor for aerial agents.
        
        Args:
            sensor_range: Maximum slant distance from drone to detected point
            fov: Field of view angle in radians (half-angle of cone)
        """
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._data: Dict[str, Union[Dict[int, Node], List[OSMEdge]]] = {}
        self._owner = None
        self.range = sensor_range
        self.fov = min(fov, math.pi * 0.9)  # Cap at ~162° to avoid backward vision
        self.quat = quat

    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return SensorType.AERIAL

    @property
    def data(self) -> Dict[str, Union[Dict[int, Node], List[OSMEdge]]]:
        return self._data
    
    def set_owner(self, owner: Union[str, None]) -> None:
        if owner is not None:
            agent = self.ctx.agent.get_agent(owner)
            if agent.type != AgentType.AERIAL:
                raise ValueError("Owner of AerialSensor must be an aerial agent")
        self._owner = owner

    def sense(self, node_id: int) -> None:
        """
        Detect nodes within the conic field of view from the drone's position.
        
        Args:
            node_id: Current node (may not be used if drone is airborne)
        """        
        # If no owner, return empty
        if self._owner is None:
            self._data = {'nodes': {}, 'edges': []}
            return
        agent = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner))

        # Multiply agent orientation by sensor quaternion
        orientation = multiply_quaternions(agent.quat, self.quat)
        # Convert to Euler angles to extract pitch
        fx, fy, fz = quaternion_to_direction(orientation)

        pos = agent.position
                
        x, y, z = pos
        
        # Calculate the radius of visibility on the ground
        # Based on cone geometry and sensor range constraints
        half_angle = self.fov / 2

        sensed_nodes: Dict[int, Node] = {}
        sensed_edges: List[OSMEdge] = []

        for edge_id in self.ctx.graph.graph.get_edges(d=self.range, x=x, y=y):
            edge = self.ctx.graph.graph.get_edge(edge_id)
            source = self.ctx.graph.graph.get_node(edge.source)
            target = self.ctx.graph.graph.get_node(edge.target)
            # Check if either endpoint is within range
            normsq = (source.x - x)**2 + (source.y - y)**2 + z**2
            cosine = (source.x - x) * fx + (source.y - y) * fy - z * fz
            angle = math.acos(max(min(cosine/math.sqrt(normsq), 1.0), -1.0)) if normsq != 0 else 2*math.pi
            sbool = (normsq <= self.range**2) and (angle <= half_angle)
            normsq = (target.x - x)**2 + (target.y - y)**2 + z**2
            cosine = (target.x - x) * fx + (target.y - y) * fy - z * fz
            angle = math.acos(max(min(cosine/math.sqrt(normsq), 1.0), -1.0)) if normsq != 0 else 2*math.pi
            tbool = (normsq <= self.range**2) and (angle <= half_angle)
            # Check if angle between node vector and downward vertical is within FOV
            if sbool:
                sensed_nodes[source.id] = source
            if tbool:
                sensed_nodes[target.id] = target
            if sbool and tbool:
                sensed_edges.append(edge)
        
        self._data = {'nodes': sensed_nodes, 'edges': sensed_edges}

    def update(self, data: Dict[str, Any]) -> None:
        pass


class AerialAgentSensor(ISensor):
    def __init__(
        self, 
        ctx: IContext, 
        sensor_id: str, 
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
        self.range = sensor_range
        self.fov = fov              
        self.quat = quat  
        self._owner = None
        self._data: Dict[str, Tuple[AgentType, Tuple[float, float, float]]] = {}
    
    @property
    def sensor_id(self) -> str:
        return self._sensor_id
    
    @property
    def type(self) -> SensorType:
        return SensorType.AERIAL_AGENT

    @property
    def data(self) -> Dict[str, Tuple[float, float, float]]:
        return self._data

    def set_owner(self, owner: Union[str, None]) -> None:
        agent = self.ctx.agent.get_agent(owner) if owner else None
        if agent is not None:
            if agent.type != AgentType.AERIAL:
                raise ValueError("Owner of AerialAgentSensor must be an aerial agent")
        self._owner = owner
            
    def sense(self, node_id: int) -> None:
        """
        Detects agents within the sensor range in 3D space.
        Returns agent positions instead of node IDs for aerial agents.
        """
        # Get sensing position
        if self._owner is None:
            self._data = {}
            return
        agent = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner))
        quat = multiply_quaternions(agent.quat, self.quat)
        fx, fy, fz = quaternion_to_direction(quat)

        x, y, z = agent.position

        sensed_agents = {}

        # Check all agents except the owner
        for agent in self.ctx.agent.create_iter():
            if agent.name == self._owner:
                continue
            
            # Get agent position
            if agent.type == AgentType.AERIAL:
                agent_pos = cast(IAerialAgent, agent).position
            elif agent.type == AgentType.BASIC:
                agent_node = self.ctx.graph.graph.get_node(agent.current_node_id)
                agent_pos = (agent_node.x, agent_node.y, 0.0)
            else:
                raise RuntimeError(f"Unknown agent type {agent.type} for agent {agent.name}")
            
            # Calculate 3D distance
            dx = agent_pos[0] - x
            dy = agent_pos[1] - y
            dz = agent_pos[2] - z
            distance_3d = dx**2 + dy**2 + dz**2

            cosine = dx * fx + dy * fy + dz * fz
            angle = math.acos(max(min(cosine/math.sqrt(distance_3d), 1.0), -1.0)) if distance_3d != 0 else 2*math.pi
            # Check range and FOV
            agent_bool = (distance_3d <= self.range**2) and (angle <= self.fov / 2)

            if agent_bool:
                sensed_agents[agent.name] = (agent.type, agent_pos)

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
        elif sensor_type == SensorType.AERIAL:
            sensor = AerialSensor(
                self.ctx, sensor_id,
                sensor_range=cast(float, kwargs.get('sensor_range', 100.0)),
                fov=cast(float, kwargs.get('fov', math.pi/3)),  # Default 60° FOV
                quat=kwargs.get('quat', (0.0, 0.0, 1.0, 0.0))  # Default downward-facing
            )
        elif sensor_type == SensorType.AERIAL_AGENT:
            sensor = AerialAgentSensor(
                self.ctx, sensor_id,
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
            self.ctx.logger.warning(f"SensorType {name} already exists. Type has been set previously in current process.")
        else:
            extend_enum(SensorType, name, len(SensorType))
        val = getattr(SensorType, name)
        def decorator(cls_type: ISensor) -> ISensor:
            cls_type.type = property(lambda obj: val)
            return cls_type
        return decorator

    def terminate(self):
        return
