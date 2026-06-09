"""Basic ground-level sensors: NeighborSensor, MapSensor, AgentSensor."""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

from gamms.typing import (
    IContext,
    ISensor,
    Node,
    OSMEdge,
    SensorType,
)


class NeighborSensor(ISensor):
    def __init__(self, ctx: IContext, sensor_id: str, sensor_type: SensorType):
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._type = sensor_type
        self._data: List[int] = []
        self._owner: Optional[str] = None

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
        nearest_neighbors = {node_id}
        for nid in self.ctx.graph.graph.get_neighbors(node_id):
            nearest_neighbors.add(nid)
        self._data = list(nearest_neighbors)

    def update(self, data: Dict[str, Any]) -> None:
        pass


class MapSensor(ISensor):
    def __init__(
        self,
        ctx: IContext,
        sensor_id: str,
        sensor_type: SensorType,
        sensor_range: float,
        fov: float,
        orientation: Tuple[float, float] = (1.0, 0.0),
    ):
        """
        Acts as a map sensor (range == inf), a range sensor (fov == 2π),
        or a unidirectional sensor (fov < 2π). FOV/orientation in radians.
        """
        self.ctx = ctx
        self._sensor_id = sensor_id
        self._type = sensor_type
        self.range = sensor_range
        self.fov = fov
        norm = math.sqrt(orientation[0]**2 + orientation[1]**2)
        self.orientation = (orientation[0] / norm, orientation[1] / norm)
        self._data: Dict[str, Union[Dict[int, Node], List[OSMEdge]]] = {}
        self._owner: Optional[str] = None

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

    def sense(self, node_id: int) -> None:
        current_node = self.ctx.graph.graph.get_node(node_id)
        if self._owner is not None:
            owner_orientation = self.ctx.agent.get_agent(self._owner).orientation
            orientation_used = (
                self.orientation[0] * owner_orientation[0] - self.orientation[1] * owner_orientation[1],
                self.orientation[0] * owner_orientation[1] + self.orientation[1] * owner_orientation[0],
            )
        else:
            orientation_used = self.orientation

        if self.range == float('inf'):
            edge_iter = self.ctx.graph.graph.get_edges()
        else:
            edge_iter = self.ctx.graph.graph.get_edges(d=self.range, x=current_node.x, y=current_node.y)

        sensed_nodes: Dict[int, Node] = {}
        sensed_edges: List[OSMEdge] = []

        range_sq = self.range ** 2 if self.range != float('inf') else float('inf')

        for edge_id in edge_iter:
            edge = self.ctx.graph.graph.get_edge(edge_id)
            source = self.ctx.graph.graph.get_node(edge.source)
            target = self.ctx.graph.graph.get_node(edge.target)
            sbool = (source.x - current_node.x)**2 + (source.y - current_node.y)**2 <= range_sq
            tbool = (target.x - current_node.x)**2 + (target.y - current_node.y)**2 <= range_sq
            if not (self.fov == 2 * math.pi or orientation_used == (0.0, 0.0)):
                angle = math.atan2(source.y - current_node.y, source.x - current_node.x) - math.atan2(orientation_used[1], orientation_used[0]) + math.pi
                angle = (angle % (2 * math.pi)) - math.pi
                sbool &= (abs(angle) <= self.fov / 2) or (source.id == node_id)
                angle = math.atan2(target.y - current_node.y, target.x - current_node.x) - math.atan2(orientation_used[1], orientation_used[0]) + math.pi
                angle = (angle % (2 * math.pi)) - math.pi
                tbool &= (abs(angle) <= self.fov / 2) or (target.id == node_id)
            if sbool:
                sensed_nodes[source.id] = source
            if tbool:
                sensed_nodes[target.id] = target
            if sbool and tbool:
                sensed_edges.append(edge)

        self._data = {'nodes': sensed_nodes, 'edges': sensed_edges}

    def update(self, data: Dict[str, Any]) -> None:
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
        owner: Optional[str] = None,
    ):
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
        current_node = self.ctx.graph.graph.get_node(node_id)
        if self._owner is not None:
            owner_orientation = self.ctx.agent.get_agent(self._owner).orientation
            orientation_used = (
                self.orientation[0] * owner_orientation[0] - self.orientation[1] * owner_orientation[1],
                self.orientation[0] * owner_orientation[1] + self.orientation[1] * owner_orientation[0],
            )
        else:
            orientation_used = self.orientation

        sensed_agents: Dict[str, int] = {}
        range_sq = self.range ** 2 if self.range != float('inf') else float('inf')

        for agent in self.ctx.agent.create_iter():
            if agent.name == self._owner:
                continue
            agent_node = self.ctx.graph.graph.get_node(agent.current_node_id)
            distance_sq = (agent_node.x - current_node.x)**2 + (agent_node.y - current_node.y)**2

            if distance_sq <= range_sq:
                if self.fov == 2 * math.pi or orientation_used == (0.0, 0.0):
                    sensed_agents[agent.name] = agent.current_node_id
                else:
                    angle = math.atan2(agent_node.y - current_node.y, agent_node.x - current_node.x) - math.atan2(orientation_used[1], orientation_used[0]) + math.pi
                    angle = (angle % (2 * math.pi)) - math.pi
                    if abs(angle) <= self.fov / 2 or agent.current_node_id == node_id:
                        sensed_agents[agent.name] = agent.current_node_id

        self._data = sensed_agents

    def update(self, data: Dict[str, Any]) -> None:
        pass
