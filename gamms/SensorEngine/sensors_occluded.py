"""Occlusion-aware sensors and the geometry primitives they depend on."""

import math
from typing import Any, Dict, Iterator, List, Optional, Tuple, cast

import numpy as np

from gamms.typing import (
    AgentType,
    IAerialAgent,
    IContext,
    Node,
    SensorType,
)
from gamms.SensorEngine.sensors_basic import AgentSensor, MapSensor
from gamms.SensorEngine.sensors_aerial import AerialAgentSensor, AerialSensor


Vec3 = Tuple[float, float, float]

_FACE_BATCH = 64   # faces processed per numpy kernel call


# ---------------------------------------------------------------------------
# Scalar Möller-Trumbore — used by agent sensors (early-exit per agent)
# ---------------------------------------------------------------------------

def _segment_triangle(
    a: Vec3, b: Vec3,
    v0: Vec3, v1: Vec3, v2: Vec3,
) -> bool:
    """True if segment a→b intersects triangle v0-v1-v2."""
    EPS = 1e-9
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    e1x = v1[0] - v0[0]; e1y = v1[1] - v0[1]; e1z = v1[2] - v0[2]
    e2x = v2[0] - v0[0]; e2y = v2[1] - v0[1]; e2z = v2[2] - v0[2]
    hx = dy * e2z - dz * e2y
    hy = dz * e2x - dx * e2z
    hz = dx * e2y - dy * e2x
    a_val = e1x * hx + e1y * hy + e1z * hz
    if abs(a_val) < EPS:
        return False
    f = 1.0 / a_val
    sx = a[0] - v0[0]; sy = a[1] - v0[1]; sz = a[2] - v0[2]
    u = f * (sx * hx + sy * hy + sz * hz)
    if u < 0.0 or u > 1.0:
        return False
    qx = sy * e1z - sz * e1y
    qy = sz * e1x - sx * e1z
    qz = sx * e1y - sy * e1x
    v = f * (dx * qx + dy * qy + dz * qz)
    if v < 0.0 or u + v > 1.0:
        return False
    t = f * (e2x * qx + e2y * qy + e2z * qz)
    return 0.0 <= t <= 1.0


def _quad_blocks(a: Vec3, b: Vec3, face: Any) -> bool:
    """True if segment a→b is blocked by the ObsFace quad."""
    tl, tr, br, bl = face.tl, face.tr, face.br, face.bl
    return _segment_triangle(a, b, tl, tr, br) or _segment_triangle(a, b, tl, br, bl)


# ---------------------------------------------------------------------------
# Vectorised kernels — N nodes × 1 face  (kept for tests)
# ---------------------------------------------------------------------------

def _triangle_blocks_batch(
    O: np.ndarray,   # (3,)
    T: np.ndarray,   # (N, 3)
    v0: np.ndarray,  # (3,)
    v1: np.ndarray,  # (3,)
    v2: np.ndarray,  # (3,)
) -> np.ndarray:     # (N,) bool
    """Which of the N segments O→T[i] hit the triangle."""
    EPS = 1e-9
    D  = T - O
    e1 = v1 - v0
    e2 = v2 - v0
    h  = np.cross(D, e2)
    a  = h @ e1
    valid = np.abs(a) > EPS
    result = np.zeros(len(T), dtype=bool)
    if not valid.any():
        return result
    inv_a = np.where(valid, 1.0 / np.where(valid, a, 1.0), 0.0)
    s = O - v0
    u = inv_a * (h @ s)
    q = np.cross(s, e1)
    v = inv_a * (D @ q)
    t = inv_a * float(np.dot(e2, q))
    return valid & (u >= 0.0) & (u <= 1.0) & (v >= 0.0) & (u + v <= 1.0) & (t >= 0.0) & (t <= 1.0)


def _quad_blocks_batch(
    O: np.ndarray,  # (3,)
    T: np.ndarray,  # (N, 3)
    face: Any,
) -> np.ndarray:    # (N,) bool
    """Which of the N segments O→T[i] are blocked by the ObsFace quad."""
    if len(T) == 0:
        return np.zeros(0, dtype=bool)
    tl = np.array(face.tl, dtype=float)
    tr = np.array(face.tr, dtype=float)
    br = np.array(face.br, dtype=float)
    bl = np.array(face.bl, dtype=float)
    blocked = _triangle_blocks_batch(O, T, tl, tr, br)
    remaining = ~blocked
    if remaining.any():
        blocked[remaining] = _triangle_blocks_batch(O, T[remaining], tl, br, bl)
    return blocked


# ---------------------------------------------------------------------------
# Vectorised kernel — F faces × N nodes  (map/aerial sensor batch path)
# ---------------------------------------------------------------------------

def _tri_block_FN(
    obs: np.ndarray,      # (3,)
    targets: np.ndarray,  # (N, 3)
    v0: np.ndarray,       # (F, 3)
    v1: np.ndarray,       # (F, 3)
    v2: np.ndarray,       # (F, 3)
) -> np.ndarray:          # (F, N) bool
    """Möller-Trumbore for F triangles against N segments simultaneously."""
    EPS = 1e-9
    D  = targets - obs
    e1 = v1 - v0
    e2 = v2 - v0
    h  = np.cross(D[np.newaxis], e2[:, np.newaxis])        # (F, N, 3)
    a  = np.einsum('fni,fi->fn', h, e1)                    # (F, N)
    valid = np.abs(a) > EPS
    inv_a = np.where(valid, 1.0 / np.where(valid, a, 1.0), 0.0)
    s = obs - v0                                            # (F, 3)
    u = inv_a * np.einsum('fni,fi->fn', h, s)              # (F, N)
    q = np.cross(s, e1)                                    # (F, 3)
    v = inv_a * (D @ q.T).T                                # (F, N)
    t = inv_a * np.einsum('fi,fi->f', e2, q)[:, np.newaxis]
    return valid & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)


def _chunk_blocks(
    obs: np.ndarray,      # (3,)
    targets: np.ndarray,  # (N, 3)
    faces: list,
) -> np.ndarray:          # (N,) bool
    """Vectorise a batch of ≤ _FACE_BATCH faces against N targets."""
    if not faces or len(targets) == 0:
        return np.zeros(len(targets), dtype=bool)
    tl = np.array([f.tl for f in faces], dtype=float)
    tr = np.array([f.tr for f in faces], dtype=float)
    br = np.array([f.br for f in faces], dtype=float)
    bl = np.array([f.bl for f in faces], dtype=float)
    return (
        _tri_block_FN(obs, targets, tl, tr, br) |
        _tri_block_FN(obs, targets, tl, br, bl)
    ).any(axis=0)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _iter_faces(graph_engine: Any, x: float, y: float, radius: float) -> Iterator[Any]:
    """Stream ObsFace objects from the graph engine, spatially filtered."""
    try:
        face_ids: Iterator[int] = (
            graph_engine.get_obstacle_faces(radius, x, y)
            if math.isfinite(radius) and radius >= 0
            else graph_engine.get_obstacle_faces()
        )
    except (RuntimeError, TypeError):
        return
    for fid in face_ids:
        try:
            yield graph_engine.get_obstacle_face(fid)
        except KeyError:
            continue


def _apply_occlusion(
    obs: np.ndarray,
    targets: np.ndarray,
    face_iter: Iterator[Any],
) -> np.ndarray:
    """Stream faces in chunks, returning a (N,) visible bool array."""
    visible = np.ones(len(targets), dtype=bool)
    chunk: List[Any] = []
    for face in face_iter:
        chunk.append(face)
        if len(chunk) == _FACE_BATCH:
            idx = np.where(visible)[0]
            visible[idx[_chunk_blocks(obs, targets[idx], chunk)]] = False
            chunk.clear()
            if not visible.any():
                return visible
    if chunk:
        idx = np.where(visible)[0]
        if len(idx):
            visible[idx[_chunk_blocks(obs, targets[idx], chunk)]] = False
    return visible


def _filter_data(data: dict, node_ids: list, visible: np.ndarray) -> dict:
    """Rebuild sensor _data keeping only visible nodes and edges between them."""
    visible_ids = {node_ids[i] for i, v in enumerate(visible) if v}
    return {
        'nodes': {nid: data['nodes'][nid] for nid in visible_ids},
        'edges': [e for e in data.get('edges', [])
                  if e.source in visible_ids and e.target in visible_ids],
    }


# ---------------------------------------------------------------------------
# Sensor classes
# ---------------------------------------------------------------------------

class OccludedMapSensor(MapSensor):
    """MapSensor that drops nodes/edges occluded by obstacle faces."""

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

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        nodes: Dict[int, Node] = self._data.get('nodes', {})
        if not nodes:
            return

        current_node = self.ctx.graph.graph.get_node(node_id)
        origin: Vec3 = (current_node.x, current_node.y, self.observer_height)
        node_ids = list(nodes)
        obs     = np.array(origin, dtype=float)
        targets = np.array(
            [(nodes[nid].x, nodes[nid].y, self.observer_height) for nid in node_ids],
            dtype=float,
        )
        visible = _apply_occlusion(
            obs, targets,
            _iter_faces(self.ctx.graph, origin[0], origin[1], self.range),
        )
        self._data = _filter_data(self._data, node_ids, visible)


class OccludedAgentSensor(AgentSensor):
    """AgentSensor that drops agents hidden behind obstacle faces."""

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

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        if not self._data:
            return

        current_node = self.ctx.graph.graph.get_node(node_id)
        origin: Vec3 = (current_node.x, current_node.y, self.observer_height)
        faces  = list(_iter_faces(self.ctx.graph, origin[0], origin[1], self.range))

        kept: Dict[str, int] = {}
        for agent_name, agent_node_id in self._data.items():
            agent_node = self.ctx.graph.graph.get_node(agent_node_id)
            target = (agent_node.x, agent_node.y, self.observer_height)
            if not any(_quad_blocks(origin, target, f) for f in faces):
                kept[agent_name] = agent_node_id
        self._data = kept


class OccludedAerialSensor(AerialSensor):
    """AerialSensor that drops ground nodes/edges occluded by obstacle faces."""

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        if self._owner is None:
            return
        nodes: Dict[int, Node] = self._data.get('nodes', {})
        if not nodes:
            return

        origin   = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner)).position
        node_ids = list(nodes)
        obs      = np.array(origin, dtype=float)
        targets  = np.array(
            [(nodes[nid].x, nodes[nid].y, 0.0) for nid in node_ids],
            dtype=float,
        )
        visible = _apply_occlusion(
            obs, targets,
            _iter_faces(self.ctx.graph, origin[0], origin[1], self.range),
        )
        self._data = _filter_data(self._data, node_ids, visible)


class OccludedAerialAgentSensor(AerialAgentSensor):
    """AerialAgentSensor that drops occluded agents — early exit per agent."""

    def sense(self, node_id: int) -> None:
        super().sense(node_id)
        if self._owner is None:
            return
        if not self._data:
            return

        origin = cast(IAerialAgent, self.ctx.agent.get_agent(self._owner)).position
        faces  = list(_iter_faces(self.ctx.graph, origin[0], origin[1], self.range))

        kept: Dict[str, Tuple[AgentType, Tuple[float, float, float]]] = {}
        for name, (atype, pos) in self._data.items():
            if not any(_quad_blocks(origin, pos, f) for f in faces):
                kept[name] = (atype, pos)
        self._data = kept
