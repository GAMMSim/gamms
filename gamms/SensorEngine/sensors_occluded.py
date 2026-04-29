"""Occlusion-aware sensors. One general class per axis.

The factory wires the backward-compat ``OCCLUDED_RANGE`` / ``OCCLUDED_ARC``
/ ``OCCLUDED_AGENT_RANGE`` / ``OCCLUDED_AGENT_ARC`` enum values to these
classes with the appropriate kwargs — there is no longer a separate class
per arc/range variant.
"""

import math
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, cast

from gamms.typing import (
    AgentType,
    IAerialAgent,
    IContext,
    Node,
    OSMEdge,
    SensorType,
)
from gamms.SensorEngine.sensors_basic import AgentSensor, MapSensor
from gamms.SensorEngine.sensors_aerial import AerialAgentSensor, AerialSensor
from gamms.SensorEngine.occlusion import segment_blocked_by_polygon


def _polygons_in_range(
    ctx: IContext,
    x: float,
    y: float,
    radius: float,
) -> List[Dict[str, Any]]:
    """Pull polygon records whose bbox overlaps the sensor range.

    Falls back to scanning all polygons when the graph engine doesn't
    expose a range-aware ``get_polygons`` (older custom engines).
    """
    graph_engine = ctx.graph
    if graph_engine is None:
        return []
    get_polygons = getattr(graph_engine, "get_polygons", None)
    get_polygon = getattr(graph_engine, "get_polygon", None)
    if not callable(get_polygons) or not callable(get_polygon):
        return []
    try:
        if math.isfinite(radius) and radius >= 0:
            ids = list(get_polygons(radius, x, y))
        else:
            ids = list(get_polygons())
    except (RuntimeError, TypeError):
        try:
            ids = list(get_polygons())
        except RuntimeError:
            return []

    polygons: List[Dict[str, Any]] = []
    for pid in ids:
        try:
            polygons.append(get_polygon(pid))
        except KeyError:
            continue
    return polygons


def _is_blocked(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
    polygons: Iterable[Dict[str, Any]],
) -> bool:
    for poly in polygons:
        if segment_blocked_by_polygon(a, b, poly["coords"], poly.get("base", 0.0), poly["height"]):
            return True
    return False


class OccludedMapSensor(MapSensor):
    """``MapSensor`` variant that drops nodes/edges occluded by polygons.

    Single class for ``OCCLUDED_MAP`` / ``OCCLUDED_RANGE`` / ``OCCLUDED_ARC``;
    the variants differ only in the (range, fov) preset wired by the factory.
    """

    def __init__(
        self,
        ctx: IContext,
        sensor_id: str,
        sensor_type: SensorType,
        sensor_range: float,
        fov: float,
        orientation: Tuple[float, float] = (1.0, 0.0),
        observer_height: float = 1.6,
    ) -> None:
        super().__init__(ctx, sensor_id, sensor_type, sensor_range, fov, orientation)
        self.observer_height = observer_height

    def _origin(self, current_node: Node) -> Tuple[float, float, float]:
        if self._owner is not None:
            agent = self.ctx.agent.get_agent(self._owner)
            if getattr(agent, "type", None) == AgentType.AERIAL:
                return cast(IAerialAgent, agent).position
        return (current_node.x, current_node.y, self.observer_height)

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        current_node = self.ctx.graph.graph.get_node(node_id)
        origin = self._origin(current_node)
        polygons = _polygons_in_range(self.ctx, origin[0], origin[1], self.range)
        if not polygons:
            return
        nodes = self._data.get('nodes', {})
        edges = self._data.get('edges', [])
        visible_nodes: Dict[int, Node] = {}
        for nid, node in nodes.items():
            target = (node.x, node.y, self.observer_height)
            if not _is_blocked(origin, target, polygons):
                visible_nodes[nid] = node
        visible_edges: List[OSMEdge] = []
        for edge in edges:
            if edge.source in visible_nodes and edge.target in visible_nodes:
                visible_edges.append(edge)
        self._data = {'nodes': visible_nodes, 'edges': visible_edges}


class OccludedAgentSensor(AgentSensor):
    """``AgentSensor`` variant that drops agents hidden behind polygons.

    Single class for ``OCCLUDED_AGENT`` / ``OCCLUDED_AGENT_RANGE`` /
    ``OCCLUDED_AGENT_ARC``.
    """

    def __init__(
        self,
        ctx: IContext,
        sensor_id: str,
        sensor_type: SensorType,
        sensor_range: float,
        fov: float = 2 * math.pi,
        orientation: Tuple[float, float] = (1.0, 0.0),
        owner: Optional[str] = None,
        observer_height: float = 1.6,
    ) -> None:
        super().__init__(ctx, sensor_id, sensor_type, sensor_range, fov, orientation, owner)
        self.observer_height = observer_height

    def _origin(self, current_node: Node) -> Tuple[float, float, float]:
        if self._owner is not None:
            agent = self.ctx.agent.get_agent(self._owner)
            if getattr(agent, "type", None) == AgentType.AERIAL:
                return cast(IAerialAgent, agent).position
        return (current_node.x, current_node.y, self.observer_height)

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        current_node = self.ctx.graph.graph.get_node(node_id)
        origin = self._origin(current_node)
        polygons = _polygons_in_range(self.ctx, origin[0], origin[1], self.range)
        if not polygons:
            return
        kept: Dict[str, int] = {}
        for agent_name, agent_node_id in self._data.items():
            agent_node = self.ctx.graph.graph.get_node(agent_node_id)
            target = (agent_node.x, agent_node.y, self.observer_height)
            if not _is_blocked(origin, target, polygons):
                kept[agent_name] = agent_node_id
        self._data = kept


class OccludedAerialSensor(AerialSensor):
    """``AerialSensor`` variant that drops occluded ground nodes/edges."""

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        if self._owner is None:
            return
        agent = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner))
        origin = agent.position
        polygons = _polygons_in_range(self.ctx, origin[0], origin[1], self.range)
        if not polygons:
            return
        nodes = self._data.get('nodes', {})
        edges = self._data.get('edges', [])
        visible_nodes: Dict[int, Node] = {}
        for nid, node in nodes.items():
            target = (node.x, node.y, 0.0)
            if not _is_blocked(origin, target, polygons):
                visible_nodes[nid] = node
        visible_edges: List[OSMEdge] = []
        for edge in edges:
            if edge.source in visible_nodes and edge.target in visible_nodes:
                visible_edges.append(edge)
        self._data = {'nodes': visible_nodes, 'edges': visible_edges}


class OccludedAerialAgentSensor(AerialAgentSensor):
    """``AerialAgentSensor`` variant that drops occluded agents."""

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        if self._owner is None:
            return
        agent = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner))
        origin = agent.position
        polygons = _polygons_in_range(self.ctx, origin[0], origin[1], self.range)
        if not polygons:
            return
        kept: Dict[str, Tuple[AgentType, Tuple[float, float, float]]] = {}
        for name, (atype, pos) in self._data.items():
            target = (pos[0], pos[1], pos[2])
            if not _is_blocked(origin, target, polygons):
                kept[name] = (atype, pos)
        self._data = kept
