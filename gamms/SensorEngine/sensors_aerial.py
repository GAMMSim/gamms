"""Aerial sensors: AerialSensor, AerialAgentSensor, plus quaternion helpers."""

import math
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from gamms.typing import (
    AgentType,
    IAerialAgent,
    IContext,
    ISensor,
    Node,
    OSMEdge,
    SensorType,
)


def multiply_quaternions(
    q1: Tuple[float, float, float, float],
    q2: Tuple[float, float, float, float],
) -> Tuple[float, float, float, float]:
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    )


def quaternion_to_direction(
    quat: Tuple[float, float, float, float],
) -> Tuple[float, float, float]:
    w, x, y, z = quat
    return (
        1 - 2*(y**2 + z**2),
        2*(x*y + w*z),
        2*(x*z - w*y),
    )


class AerialSensor(ISensor):
    def __init__(
        self,
        ctx: IContext,
        sensor_id: str,
        sensor_range: float,
        fov: float = math.pi / 3,
        quat: Tuple[float, float, float, float] = (math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0),
    ):
        """
        Downward-facing conic sensor for aerial agents.
        """
        self._sensor_id = sensor_id
        self.ctx = ctx
        self._data: Dict[str, Union[Dict[int, Node], List[OSMEdge]]] = {}
        self._owner: Optional[str] = None
        self.range = sensor_range
        self.fov = min(fov, math.pi * 0.9)
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
        if self._owner is None:
            self._data = {'nodes': {}, 'edges': []}
            return
        agent = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner))
        orientation = multiply_quaternions(agent.quat, self.quat)
        fx, fy, fz = quaternion_to_direction(orientation)
        x, y, z = agent.position
        half_angle = self.fov / 2

        sensed_nodes: Dict[int, Node] = {}
        sensed_edges: List[OSMEdge] = []

        for edge_id in self.ctx.graph.graph.get_edges(d=self.range, x=x, y=y):
            edge = self.ctx.graph.graph.get_edge(edge_id)
            source = self.ctx.graph.graph.get_node(edge.source)
            target = self.ctx.graph.graph.get_node(edge.target)

            normsq = (source.x - x)**2 + (source.y - y)**2 + z**2
            cosine = (source.x - x) * fx + (source.y - y) * fy - z * fz
            angle = math.acos(max(min(cosine / math.sqrt(normsq), 1.0), -1.0)) if normsq != 0 else 2 * math.pi
            sbool = (normsq <= self.range**2) and (angle <= half_angle)

            normsq = (target.x - x)**2 + (target.y - y)**2 + z**2
            cosine = (target.x - x) * fx + (target.y - y) * fy - z * fz
            angle = math.acos(max(min(cosine / math.sqrt(normsq), 1.0), -1.0)) if normsq != 0 else 2 * math.pi
            tbool = (normsq <= self.range**2) and (angle <= half_angle)

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
        quat: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0),
    ):
        self._sensor_id = sensor_id
        self.ctx = ctx
        self.range = sensor_range
        self.fov = fov
        self.quat = quat
        self._owner: Optional[str] = None
        self._data: Dict[str, Tuple[AgentType, Tuple[float, float, float]]] = {}

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    @property
    def type(self) -> SensorType:
        return SensorType.AERIAL_AGENT

    @property
    def data(self) -> Dict[str, Tuple[AgentType, Tuple[float, float, float]]]:
        return self._data

    def set_owner(self, owner: Union[str, None]) -> None:
        agent = self.ctx.agent.get_agent(owner) if owner else None
        if agent is not None:
            if agent.type != AgentType.AERIAL:
                raise ValueError("Owner of AerialAgentSensor must be an aerial agent")
        self._owner = owner

    def sense(self, node_id: int) -> None:
        if self._owner is None:
            self._data = {}
            return
        agent = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner))
        quat = multiply_quaternions(agent.quat, self.quat)
        fx, fy, fz = quaternion_to_direction(quat)
        x, y, z = agent.position

        sensed_agents: Dict[str, Tuple[AgentType, Tuple[float, float, float]]] = {}
        for other in self.ctx.agent.create_iter():
            if other.name == self._owner:
                continue
            if other.type == AgentType.AERIAL:
                agent_pos = cast(IAerialAgent, other).position
            elif other.type == AgentType.BASIC:
                agent_node = self.ctx.graph.graph.get_node(other.current_node_id)
                agent_pos = (agent_node.x, agent_node.y, 0.0)
            else:
                raise RuntimeError(f"Unknown agent type {other.type} for agent {other.name}")

            dx = agent_pos[0] - x
            dy = agent_pos[1] - y
            dz = agent_pos[2] - z
            distance_3d = dx**2 + dy**2 + dz**2
            cosine = dx * fx + dy * fy + dz * fz
            angle = math.acos(max(min(cosine / math.sqrt(distance_3d), 1.0), -1.0)) if distance_3d != 0 else 2 * math.pi
            if (distance_3d <= self.range**2) and (angle <= self.fov / 2):
                sensed_agents[other.name] = (other.type, agent_pos)

        self._data = sensed_agents

    def update(self, data: Dict[str, Any]) -> None:
        pass
