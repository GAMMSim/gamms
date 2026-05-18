"""Occlusion-aware sensors and the geometry primitives they depend on.

Geometry helpers
----------------
Each obstacle face stored in the graph engine is a vertical rectangular wall:
an ``(x, y)`` edge extruded between ``base`` and ``base + height``.  Sensor
rays are tested against the trapezoidal faces that make up the lateral walls,
plus the polygon top (when the ray descends through it from above).

Sensor classes
--------------
The factory wires the backward-compat ``OCCLUDED_RANGE`` / ``OCCLUDED_ARC``
/ ``OCCLUDED_AGENT_RANGE`` / ``OCCLUDED_AGENT_ARC`` enum values to these
classes with the appropriate kwargs — there is no longer a separate class
per arc/range variant.
"""

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, cast

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


# ---------------------------------------------------------------------------
# Geometry primitives
# ---------------------------------------------------------------------------

Vec3 = Tuple[float, float, float]
Vec2 = Tuple[float, float]


def segment_intersects_trapezoid(
    a: Vec3,
    b: Vec3,
    p1: Vec2,
    p2: Vec2,
    base: float,
    height: float,
) -> bool:
    """Return True if the 3D segment ``a-b`` crosses the trapezoidal face
    spanning the wall (p1, p2) between z=base and z=base+height.

    The face has four corners::

        (p1.x, p1.y, base) -- (p2.x, p2.y, base)
        (p1.x, p1.y, top ) -- (p2.x, p2.y, top )

    Implementation: parametrise the ray with t in [0, 1], find t where it
    crosses the vertical wall plane, then check whether the corresponding
    (u, z) point lies inside the trapezoid (u in [0, 1] along the wall,
    z in [base, top]).
    """
    top = base + height
    ax, ay, az = a
    bx, by, bz = b
    dx, dy, dz = bx - ax, by - ay, bz - az

    wx, wy = p2[0] - p1[0], p2[1] - p1[1]
    nx, ny = -wy, wx
    denom = nx * dx + ny * dy
    rhs = nx * (p1[0] - ax) + ny * (p1[1] - ay)

    if abs(denom) < 1e-12:
        return False

    t = rhs / denom
    if t < 0.0 or t > 1.0:
        return False

    wlen_sq = wx * wx + wy * wy
    if wlen_sq == 0.0:
        return False
    px = ax + t * dx
    py = ay + t * dy
    u = ((px - p1[0]) * wx + (py - p1[1]) * wy) / wlen_sq
    if u < 0.0 or u > 1.0:
        return False

    z = az + t * dz
    return base <= z <= top


def _point_in_polygon(point: Vec2, polygon: Sequence[Vec2]) -> bool:
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi):
            inside = not inside
        j = i
    return inside


def segment_intersects_polygon_top(
    a: Vec3,
    b: Vec3,
    polygon: Sequence[Vec2],
    base: float,
    height: float,
) -> bool:
    """Return True if the segment crosses the top face (z = base+height)
    inside the polygon footprint.
    """
    top = base + height
    az, bz = a[2], b[2]
    if (az - top) * (bz - top) > 0:
        return False
    if az == bz:
        return False
    t = (top - az) / (bz - az)
    if t < 0.0 or t > 1.0:
        return False
    px = a[0] + t * (b[0] - a[0])
    py = a[1] + t * (b[1] - a[1])
    return _point_in_polygon((px, py), polygon)


def segment_blocked_by_polygon(
    a: Vec3,
    b: Vec3,
    polygon: Sequence[Vec2],
    base: float,
    height: float,
) -> bool:
    """True if the 3D segment a-b is blocked by the prism defined by
    ``polygon`` extruded between ``base`` and ``base+height``.

    A polygon with fewer than three vertices is silently ignored.
    """
    if len(polygon) < 3:
        return False
    if segment_intersects_polygon_top(a, b, polygon, base, height):
        return True
    n = len(polygon)
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        if segment_intersects_trapezoid(a, b, p1, p2, base, height):
            return True
    return False


def segment_blocked_by_polygons(
    a: Vec3,
    b: Vec3,
    polygons: Iterable,
) -> bool:
    """Return True if any of the supplied polygon prisms block the segment.

    ``polygons`` is an iterable of dicts with ``coords``, ``base`` and
    ``height`` keys.
    """
    for poly in polygons:
        coords = poly.get("coords") if isinstance(poly, dict) else poly[0]
        base = poly.get("base", 0.0) if isinstance(poly, dict) else poly[1]
        height = poly.get("height", 0.0) if isinstance(poly, dict) else poly[2]
        if segment_blocked_by_polygon(a, b, coords, base, height):
            return True
    return False


# ---------------------------------------------------------------------------
# Sensor helpers
# ---------------------------------------------------------------------------

def _faces_in_range(
    ctx: IContext,
    x: float,
    y: float,
    radius: float,
) -> List[Any]:
    """Pull ObsFace records whose bbox overlaps the sensor range."""
    graph_engine = ctx.graph
    if graph_engine is None:
        return []
    try:
        if math.isfinite(radius) and radius >= 0:
            ids = list(graph_engine.get_obstacle_faces(radius, x, y))
        else:
            ids = list(graph_engine.get_obstacle_faces())
    except (RuntimeError, TypeError):
        return []
    faces: List[Any] = []
    for fid in ids:
        try:
            faces.append(graph_engine.get_obstacle_face(fid))
        except KeyError:
            continue
    return faces


def _is_blocked(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
    faces: Iterable[Any],
) -> bool:
    for face in faces:
        p1 = (face.tl[0], face.tl[1])
        p2 = (face.tr[0], face.tr[1])
        base = face.bl[2]
        height = face.tl[2] - face.bl[2]
        if segment_intersects_trapezoid(a, b, p1, p2, base, height):
            return True
    return False


# ---------------------------------------------------------------------------
# Sensor classes
# ---------------------------------------------------------------------------

class OccludedMapSensor(MapSensor):
    """``MapSensor`` variant that drops nodes/edges occluded by obstacle faces.

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
        faces = _faces_in_range(self.ctx, origin[0], origin[1], self.range)
        if not faces:
            return
        nodes = self._data.get('nodes', {})
        edges = self._data.get('edges', [])
        visible_nodes: Dict[int, Node] = {}
        for nid, node in nodes.items():
            target = (node.x, node.y, self.observer_height)
            if not _is_blocked(origin, target, faces):
                visible_nodes[nid] = node
        visible_edges: List[OSMEdge] = []
        for edge in edges:
            if edge.source in visible_nodes and edge.target in visible_nodes:
                visible_edges.append(edge)
        self._data = {'nodes': visible_nodes, 'edges': visible_edges}


class OccludedAgentSensor(AgentSensor):
    """``AgentSensor`` variant that drops agents hidden behind obstacle faces.

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
        faces = _faces_in_range(self.ctx, origin[0], origin[1], self.range)
        if not faces:
            return
        kept: Dict[str, int] = {}
        for agent_name, agent_node_id in self._data.items():
            agent_node = self.ctx.graph.graph.get_node(agent_node_id)
            target = (agent_node.x, agent_node.y, self.observer_height)
            if not _is_blocked(origin, target, faces):
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
        faces = _faces_in_range(self.ctx, origin[0], origin[1], self.range)
        if not faces:
            return
        nodes = self._data.get('nodes', {})
        edges = self._data.get('edges', [])
        visible_nodes: Dict[int, Node] = {}
        for nid, node in nodes.items():
            target = (node.x, node.y, 0.0)
            if not _is_blocked(origin, target, faces):
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
        faces = _faces_in_range(self.ctx, origin[0], origin[1], self.range)
        if not faces:
            return
        kept: Dict[str, Tuple[AgentType, Tuple[float, float, float]]] = {}
        for name, (atype, pos) in self._data.items():
            target = (pos[0], pos[1], pos[2])
            if not _is_blocked(origin, target, faces):
                kept[name] = (atype, pos)
        self._data = kept
