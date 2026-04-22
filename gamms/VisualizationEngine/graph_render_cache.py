from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import math

from gamms.typing import IGraph


class GraphSpatialIndex:
    """Uniform grid over a graph's world extent.

    Each cell holds the ids of nodes / edges whose (bounding) geometry
    overlaps the cell. Node queries are cell-exact; edge queries deduplicate
    across cells for edges whose bbox spans multiple cells.
    """

    __slots__ = ("cell_size", "x0", "y0", "nx", "ny", "node_grid", "edge_grid")

    def __init__(self, cell_size: float, x0: float, y0: float, nx: int, ny: int) -> None:
        self.cell_size = cell_size
        self.x0 = x0
        self.y0 = y0
        self.nx = nx
        self.ny = ny
        self.node_grid: List[List[int]] = [[] for _ in range(nx * ny)]
        self.edge_grid: List[List[int]] = [[] for _ in range(nx * ny)]

    def _cell(self, x: float, y: float) -> Tuple[int, int]:
        cx = int((x - self.x0) / self.cell_size)
        cy = int((y - self.y0) / self.cell_size)
        if cx < 0:
            cx = 0
        elif cx >= self.nx:
            cx = self.nx - 1
        if cy < 0:
            cy = 0
        elif cy >= self.ny:
            cy = self.ny - 1
        return cx, cy

    def add_node(self, node_id: int, x: float, y: float) -> None:
        cx, cy = self._cell(x, y)
        self.node_grid[cy * self.nx + cx].append(node_id)

    def add_edge(self, edge_id: int, x_min: float, y_min: float,
                 x_max: float, y_max: float) -> None:
        cx0, cy0 = self._cell(x_min, y_min)
        cx1, cy1 = self._cell(x_max, y_max)
        for cy in range(cy0, cy1 + 1):
            base = cy * self.nx
            for cx in range(cx0, cx1 + 1):
                self.edge_grid[base + cx].append(edge_id)

    def query_nodes(self, x_min: float, x_max: float,
                    y_min: float, y_max: float) -> Iterable[int]:
        cx0, cy0 = self._cell(x_min, y_min)
        cx1, cy1 = self._cell(x_max, y_max)
        for cy in range(cy0, cy1 + 1):
            base = cy * self.nx
            for cx in range(cx0, cx1 + 1):
                for nid in self.node_grid[base + cx]:
                    yield nid

    def query_edges(self, x_min: float, x_max: float,
                    y_min: float, y_max: float) -> Iterable[int]:
        cx0, cy0 = self._cell(x_min, y_min)
        cx1, cy1 = self._cell(x_max, y_max)
        seen = set()
        seen_add = seen.add
        for cy in range(cy0, cy1 + 1):
            base = cy * self.nx
            for cx in range(cx0, cx1 + 1):
                for eid in self.edge_grid[base + cx]:
                    if eid not in seen:
                        seen_add(eid)
                        yield eid


@dataclass
class GraphRenderCache:
    """Precomputed drawing data for a graph. Build once per graph; assign
    to :attr:`GraphData.render_cache` to share across frames."""

    edge_line_points: Dict[int, List[Tuple[float, float]]] = field(default_factory=dict)
    spatial_index: Optional[GraphSpatialIndex] = None

    @classmethod
    def build(cls, graph: IGraph) -> "GraphRenderCache":
        node_ids = list(graph.get_nodes())
        if not node_ids:
            return cls()

        nodes_by_id = {}
        x_min = math.inf
        x_max = -math.inf
        y_min = math.inf
        y_max = -math.inf
        for node_id in node_ids:
            node = graph.get_node(node_id)
            nodes_by_id[node_id] = node
            if node.x < x_min: x_min = node.x
            if node.x > x_max: x_max = node.x
            if node.y < y_min: y_min = node.y
            if node.y > y_max: y_max = node.y

        edge_ids = list(graph.get_edges())
        extent = max(x_max - x_min, y_max - y_min, 1e-6)
        target_cells = max(64, max(len(edge_ids), 1) // 16)
        n = max(8, min(128, int(math.sqrt(target_cells))))
        cell_size = extent / n

        idx = GraphSpatialIndex(cell_size, x_min, y_min, n, n)
        for node_id, node in nodes_by_id.items():
            idx.add_node(node_id, node.x, node.y)

        edge_line_points: Dict[int, List[Tuple[float, float]]] = {}
        for edge_id in edge_ids:
            edge = graph.get_edge(edge_id)
            source = nodes_by_id[edge.source]
            target = nodes_by_id[edge.target]

            if edge.linestring:
                pts: List[Tuple[float, float]] = [(source.x, source.y)]
                pts.extend((x, y) for (x, y) in edge.linestring.coords)
                pts.append((target.x, target.y))
                edge_line_points[edge.id] = pts
                ex_min = ex_max = pts[0][0]
                ey_min = ey_max = pts[0][1]
                for px, py in pts:
                    if px < ex_min: ex_min = px
                    elif px > ex_max: ex_max = px
                    if py < ey_min: ey_min = py
                    elif py > ey_max: ey_max = py
            else:
                if source.x < target.x:
                    ex_min, ex_max = source.x, target.x
                else:
                    ex_min, ex_max = target.x, source.x
                if source.y < target.y:
                    ey_min, ey_max = source.y, target.y
                else:
                    ey_min, ey_max = target.y, source.y

            idx.add_edge(edge_id, ex_min, ey_min, ex_max, ey_max)

        return cls(edge_line_points=edge_line_points, spatial_index=idx)
