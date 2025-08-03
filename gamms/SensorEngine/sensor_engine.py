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
            edge_iter = self.ctx.graph.graph.get_edges()
        else:
            edge_iter = self.ctx.graph.graph.get_edges(d=self.range, x=current_node.x, y=current_node.y)

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
