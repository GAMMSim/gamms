import os
import pickle
import sqlite3
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, Union, cast, overload

import cbor2
import networkx as nx
from shapely.geometry import LineString

from gamms.typing import IContext, IGraph, IGraphEngine, Node, OSMEdge
from gamms.typing.graph_engine import Engine
from gamms.typing.memory_engine import StoreType
from gamms.MemoryEngine.store import MemoryStore, PathLike, SqliteStore


GRAPH_STORE_NAME = "graph"
NODES_MAP = "nodes"
EDGES_MAP = "edges"
POLYGONS_MAP = "polygons"
DEFAULT_BUILDING_HEIGHT = 6.0  # ~2-storey building (metres)


_mem_Node = dataclass()(Node)


class _OSMEdge(OSMEdge):
    """Edge wrapper with a lazy ``linestring`` property.

    Geometry is stored as a tuple-of-(x, y) coordinates; we only build the
    Shapely ``LineString`` on access.
    """

    __slots__ = ("id", "source", "target", "length", "_geom")

    def __init__(self, edge_id: int, source: int, target: int, length: float, geom: Tuple[Tuple[float, float], ...]):
        self.id = edge_id
        self.source = source
        self.target = target
        self.length = length
        self._geom = geom

    @property
    def linestring(self) -> LineString:
        return LineString(self._geom)


def _normalize_polygon_coords(coords: Any) -> Tuple[Tuple[float, float], ...]:
    pts = [tuple(c) for c in coords]
    if len(pts) < 3:
        raise ValueError("Polygon must have at least 3 vertices.")
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        raise ValueError("Polygon must have at least 3 distinct vertices.")
    return tuple((float(x), float(y)) for x, y in pts)


def _polygon_bbox(coords: Tuple[Tuple[float, float], ...]) -> Tuple[float, float, float, float]:
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return (min(xs), min(ys), max(xs), max(ys))


class _GraphBase(IGraph):
    """Shared validation/normalization for both graph backends."""

    @staticmethod
    def _validate_node_data(node_data: Dict[str, Any]) -> Tuple[int, float, float]:
        if 'id' not in node_data or 'x' not in node_data or 'y' not in node_data:
            raise ValueError("Node data must include 'id', 'x', and 'y'.")
        return int(node_data['id']), float(node_data['x']), float(node_data['y'])

    @staticmethod
    def _normalize_linestring(
        edge_data: Dict[str, Any],
        get_node: Callable[[int], Node],
    ) -> Tuple[Tuple[float, float], ...]:
        linestring = edge_data.get('linestring', None)
        if linestring is None:
            source_node = get_node(edge_data['source'])
            target_node = get_node(edge_data['target'])
            return ((source_node.x, source_node.y), (target_node.x, target_node.y))
        if isinstance(linestring, LineString):
            if linestring.is_empty:
                raise ValueError(f"Invalid linestring: {linestring}")
            return tuple((float(x), float(y)) for x, y in linestring.coords)
        try:
            shaped = LineString(linestring)
            if shaped.is_empty:
                raise ValueError(f"Invalid linestring: {linestring}")
            return tuple((float(x), float(y)) for x, y in shaped.coords)
        except Exception as exc:
            raise ValueError(f"Invalid linestring data: {linestring}") from exc

    @staticmethod
    def _validate_edge_data(edge_data: Dict[str, Any]) -> None:
        for field in ('id', 'source', 'target', 'length'):
            if field not in edge_data:
                raise ValueError("Edge data must include 'id', 'source', 'target', and 'length'.")

    @staticmethod
    def _edge_bbox_from_geom(geom: Tuple[Tuple[float, float], ...]) -> Tuple[float, float, float, float]:
        xs = [c[0] for c in geom]
        ys = [c[1] for c in geom]
        return (min(xs), min(ys), max(xs), max(ys))

    def attach_networkx_graph(self, G: nx.Graph) -> None:
        for node, data in G.nodes(data=True):  # type: ignore
            node = cast(int, node)
            data = cast(Dict[str, Any], data)
            self.add_node({
                'id': node,
                'x': data.get('x', 0.0),
                'y': data.get('y', 0.0),
            })
        for u, v, data in G.edges(data=True):  # type: ignore
            u = cast(int, u)
            v = cast(int, v)
            data = cast(Dict[str, Any], data)
            self.add_edge({
                'id': data.get('id', -1),
                'source': u,
                'target': v,
                'length': data.get('length', 0.0),
                'linestring': data.get('linestring', None),
            })


class Graph(_GraphBase):
    """In-memory graph backed by a :class:`MemoryStore`."""

    def __init__(self, store: MemoryStore):
        self._store = store
        store.create_map(NODES_MAP, {'id': int, 'x': float, 'y': float}, 'id')
        store.create_map(
            EDGES_MAP,
            {
                'id': int, 'source': int, 'target': int, 'length': float,
                'geom': tuple,
                'min_x': float, 'min_y': float, 'max_x': float, 'max_y': float,
            },
            'id',
        )
        store.create_map(
            POLYGONS_MAP,
            {
                'id': int, 'coords': tuple, 'height': float, 'base': float,
                'category': str, 'attributes': dict,
                'min_x': float, 'min_y': float, 'max_x': float, 'max_y': float,
            },
            'id',
        )
        self._nodes_map: Dict[int, Dict[str, Any]] = store.get_map(NODES_MAP)
        self._edges_map: Dict[int, Dict[str, Any]] = store.get_map(EDGES_MAP)
        self._polygons_map: Dict[int, Dict[str, Any]] = store.get_map(POLYGONS_MAP)
        self._adjacency: Dict[int, Set[int]] = {}

    # ---- nodes -----------------------------------------------------------

    def add_node(self, node_data: Dict[str, Any]) -> None:
        node_id, x, y = self._validate_node_data(node_data)
        if node_id in self._nodes_map:
            raise KeyError(f"Node {node_id} already exists.")
        self._store.insert_data(NODES_MAP, {'id': node_id, 'x': x, 'y': y})
        self._adjacency.setdefault(node_id, set())

    def update_node(self, node_data: Dict[str, Any]) -> None:
        if 'id' not in node_data:
            raise ValueError("Node data must include 'id'.")
        node_id = int(node_data['id'])
        if node_id not in self._nodes_map:
            raise KeyError(f"Node {node_id} does not exist.")
        update: Dict[str, Any] = {'id': node_id}
        if 'x' in node_data:
            update['x'] = float(node_data['x'])
        if 'y' in node_data:
            update['y'] = float(node_data['y'])
        self._store.update_data(NODES_MAP, update)

    def remove_node(self, node_id: int) -> None:
        if node_id not in self._nodes_map:
            return
        edges_to_remove = [
            eid for eid, edge in self._edges_map.items()
            if edge['source'] == node_id or edge['target'] == node_id
        ]
        for eid in edges_to_remove:
            self._adjacency.get(self._edges_map[eid]['source'], set()).discard(
                self._edges_map[eid]['target']
            )
            self._store.delete_data(EDGES_MAP, eid)
        self._store.delete_data(NODES_MAP, node_id)
        self._adjacency.pop(node_id, None)
        for neighbors in self._adjacency.values():
            neighbors.discard(node_id)

    def get_node(self, node_id: int) -> Node:
        if node_id not in self._nodes_map:
            raise KeyError(f"Node {node_id} does not exist.")
        row = self._nodes_map[node_id]
        return _mem_Node(id=row['id'], x=row['x'], y=row['y'])

    @overload
    def get_nodes(self) -> Iterator[int]: ...
    @overload
    def get_nodes(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_nodes(self, d: float = -1.0, x: float = 0.0, y: float = 0.0) -> Iterator[int]:
        if d < 0:
            return iter(list(self._nodes_map.keys()))
        x_min, x_max = x - d, x + d
        y_min, y_max = y - d, y + d
        return iter([
            nid for nid, row in self._nodes_map.items()
            if x_min <= row['x'] <= x_max and y_min <= row['y'] <= y_max
        ])

    # ---- edges -----------------------------------------------------------

    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        self._validate_edge_data(edge_data)
        edge_id = int(edge_data['id'])
        if edge_id in self._edges_map:
            raise KeyError(f"Edge {edge_id} already exists.")
        source = int(edge_data['source'])
        target = int(edge_data['target'])
        if source not in self._nodes_map or target not in self._nodes_map:
            raise KeyError(
                f"Source or target node does not exist in the graph: {source}, {target}"
            )
        geom = self._normalize_linestring(edge_data, self.get_node)
        bbox = self._edge_bbox_from_geom(geom)
        self._store.insert_data(EDGES_MAP, {
            'id': edge_id,
            'source': source,
            'target': target,
            'length': float(edge_data['length']),
            'geom': geom,
            'min_x': bbox[0], 'min_y': bbox[1], 'max_x': bbox[2], 'max_y': bbox[3],
        })
        self._adjacency.setdefault(source, set()).add(target)

    def update_edge(self, edge_data: Dict[str, Any]) -> None:
        self._validate_edge_data(edge_data)
        edge_id = int(edge_data['id'])
        if edge_id not in self._edges_map:
            raise KeyError(f"Edge {edge_id} does not exist. Use add_edge to create it.")
        existing = self._edges_map[edge_id]
        self._adjacency.get(existing['source'], set()).discard(existing['target'])
        source = int(edge_data['source'])
        target = int(edge_data['target'])
        geom = self._normalize_linestring(edge_data, self.get_node)
        bbox = self._edge_bbox_from_geom(geom)
        self._store.update_data(EDGES_MAP, {
            'id': edge_id,
            'source': source,
            'target': target,
            'length': float(edge_data['length']),
            'geom': geom,
            'min_x': bbox[0], 'min_y': bbox[1], 'max_x': bbox[2], 'max_y': bbox[3],
        })
        self._adjacency.setdefault(source, set()).add(target)

    def remove_edge(self, edge_id: int) -> None:
        if edge_id not in self._edges_map:
            return
        edge = self._edges_map[edge_id]
        self._adjacency.get(edge['source'], set()).discard(edge['target'])
        self._store.delete_data(EDGES_MAP, edge_id)

    def get_edge(self, edge_id: int) -> OSMEdge:
        if edge_id not in self._edges_map:
            raise KeyError(f"Edge {edge_id} does not exist.")
        row = self._edges_map[edge_id]
        return _OSMEdge(row['id'], row['source'], row['target'], row['length'], row['geom'])

    @overload
    def get_edges(self) -> Iterator[int]: ...
    @overload
    def get_edges(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_edges(self, d: float = -1.0, x: float = 0.0, y: float = 0.0) -> Iterator[int]:
        if d < 0:
            return iter(list(self._edges_map.keys()))
        x_min, x_max = x - d, x + d
        y_min, y_max = y - d, y + d
        return iter([
            eid for eid, row in self._edges_map.items()
            if not (row['max_x'] < x_min or row['min_x'] > x_max
                    or row['max_y'] < y_min or row['min_y'] > y_max)
        ])

    def get_neighbors(self, node_id: int) -> Iterator[int]:
        if node_id not in self._nodes_map:
            raise KeyError(f"Node {node_id} does not exist.")
        for nid in self._adjacency.get(node_id, ()):
            yield nid

    # ---- polygons --------------------------------------------------------

    def add_polygon(
        self,
        polygon_id: int,
        coords: Any,
        height: float = DEFAULT_BUILDING_HEIGHT,
        base: float = 0.0,
        category: str = "building",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        if polygon_id in self._polygons_map:
            raise ValueError(f"Polygon {polygon_id} already exists.")
        if height <= 0:
            raise ValueError("Polygon height must be positive.")
        normalized = _normalize_polygon_coords(coords)
        bbox = _polygon_bbox(normalized)
        self._store.insert_data(POLYGONS_MAP, {
            'id': int(polygon_id),
            'coords': normalized,
            'height': float(height),
            'base': float(base),
            'category': str(category),
            'attributes': dict(attributes or {}),
            'min_x': bbox[0], 'min_y': bbox[1], 'max_x': bbox[2], 'max_y': bbox[3],
        })

    def get_polygon(self, polygon_id: int) -> Dict[str, Any]:
        if polygon_id not in self._polygons_map:
            raise KeyError(f"Polygon {polygon_id} does not exist.")
        row = self._polygons_map[polygon_id]
        return {
            'id': row['id'],
            'coords': list(row['coords']),
            'height': row['height'],
            'base': row['base'],
            'category': row['category'],
            'attributes': dict(row['attributes']),
        }

    @overload
    def get_polygons(self) -> Iterator[int]: ...
    @overload
    def get_polygons(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_polygons(self, d: float = -1.0, x: float = 0.0, y: float = 0.0) -> Iterator[int]:
        if d < 0:
            return iter(list(self._polygons_map.keys()))
        x_min, x_max = x - d, x + d
        y_min, y_max = y - d, y + d
        return iter([
            pid for pid, row in self._polygons_map.items()
            if not (row['max_x'] < x_min or row['min_x'] > x_max
                    or row['max_y'] < y_min or row['min_y'] > y_max)
        ])

    def remove_polygon(self, polygon_id: int) -> None:
        if polygon_id not in self._polygons_map:
            return
        self._store.delete_data(POLYGONS_MAP, polygon_id)

    # ---- persistence (in-memory only) ------------------------------------

    def save(self, path: str) -> None:
        with open(path, 'wb') as fh:
            pickle.dump({
                'nodes': dict(self._nodes_map),
                'edges': dict(self._edges_map),
                'polygons': dict(self._polygons_map),
            }, fh)

    def load(self, path: str) -> None:
        with open(path, 'rb') as fh:
            data = pickle.load(fh)
        self._nodes_map.clear()
        self._edges_map.clear()
        self._polygons_map.clear()
        self._nodes_map.update(data.get('nodes', {}))
        self._edges_map.update(data.get('edges', {}))
        self._polygons_map.update(data.get('polygons', {}))
        self._adjacency = {nid: set() for nid in self._nodes_map}
        for eid, row in self._edges_map.items():
            self._adjacency.setdefault(row['source'], set()).add(row['target'])


class SqliteGraph(_GraphBase):
    """SQLite-backed graph using a :class:`SqliteStore`."""

    def __init__(self, store: SqliteStore):
        self._store = store
        store.create_map(NODES_MAP, {'id': int, 'x': float, 'y': float}, 'id')
        store.create_map(
            EDGES_MAP,
            {
                'id': int, 'source': int, 'target': int, 'length': float,
                'geom': bytes,
                'min_x': float, 'min_y': float, 'max_x': float, 'max_y': float,
            },
            'id',
        )
        store.create_map(
            POLYGONS_MAP,
            {
                'id': int, 'coords': bytes, 'height': float, 'base': float,
                'category': str, 'attributes': bytes,
                'min_x': float, 'min_y': float, 'max_x': float, 'max_y': float,
            },
            'id',
        )
        store.create_index(NODES_MAP, ('x', 'y'))
        store.create_index(EDGES_MAP, ('source', 'target'))
        store.create_index(EDGES_MAP, ('min_x', 'min_y', 'max_x', 'max_y'),
                           name=f'idx_{EDGES_MAP}_bbox')
        store.create_index(POLYGONS_MAP, ('min_x', 'min_y', 'max_x', 'max_y'),
                           name=f'idx_{POLYGONS_MAP}_bbox')
        self._conn = store.connection()
        self._tnodes = store.table_name(NODES_MAP)
        self._tedges = store.table_name(EDGES_MAP)
        self._tpolys = store.table_name(POLYGONS_MAP)

    def _flush(self) -> None:
        self._store.flush()

    # ---- nodes -----------------------------------------------------------

    def add_node(self, node_data: Dict[str, Any]) -> None:
        node_id, x, y = self._validate_node_data(node_data)
        try:
            self._conn.execute(
                f"INSERT INTO {self._tnodes} (\"id\", \"x\", \"y\") VALUES (?, ?, ?)",
                (node_id, x, y),
            )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise KeyError(f"Node {node_id} already exists.") from exc
            raise
        self._store.mark_dirty()

    def update_node(self, node_data: Dict[str, Any]) -> None:
        node_id, x, y = self._validate_node_data(node_data)
        _ = self.get_node(node_id)
        self._conn.execute(
            f"UPDATE {self._tnodes} SET \"x\" = ?, \"y\" = ? WHERE \"id\" = ?",
            (x, y, node_id),
        )
        self._store.mark_dirty()

    def remove_node(self, node_id: int) -> None:
        self._conn.execute(
            f"DELETE FROM {self._tedges} WHERE \"source\" = ? OR \"target\" = ?",
            (node_id, node_id),
        )
        self._conn.execute(f"DELETE FROM {self._tnodes} WHERE \"id\" = ?", (node_id,))
        self._store.mark_dirty()

    def get_node(self, node_id: int) -> Node:
        self._flush()
        cursor = self._conn.cursor()
        cursor.execute(f"SELECT \"id\", \"x\", \"y\" FROM {self._tnodes} WHERE \"id\" = ?", (node_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Node {node_id} does not exist.")
        return _mem_Node(id=row[0], x=row[1], y=row[2])

    @overload
    def get_nodes(self) -> Iterator[int]: ...
    @overload
    def get_nodes(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_nodes(self, d: float = -1.0, x: float = 0.0, y: float = 0.0) -> Iterator[int]:
        self._flush()
        cursor = self._conn.cursor()
        if d >= 0:
            cursor.execute(
                f"SELECT \"id\" FROM {self._tnodes} WHERE \"x\" BETWEEN ? AND ? AND \"y\" BETWEEN ? AND ?",
                (x - d, x + d, y - d, y + d),
            )
        else:
            cursor.execute(f"SELECT \"id\" FROM {self._tnodes}")
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]

    # ---- edges -----------------------------------------------------------

    def _node_exists(self, node_id: int) -> bool:
        cursor = self._conn.execute(
            f"SELECT 1 FROM {self._tnodes} WHERE \"id\" = ?", (node_id,)
        )
        return cursor.fetchone() is not None

    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        self._validate_edge_data(edge_data)
        edge_id = int(edge_data['id'])
        source = int(edge_data['source'])
        target = int(edge_data['target'])
        self._flush()
        if not self._node_exists(source) or not self._node_exists(target):
            raise KeyError(
                f"Source or target node does not exist in the graph: {source}, {target}"
            )
        geom = self._normalize_linestring(edge_data, self.get_node)
        bbox = self._edge_bbox_from_geom(geom)
        try:
            self._conn.execute(
                f"INSERT INTO {self._tedges} (\"id\", \"source\", \"target\", \"length\", \"geom\", "
                f"\"min_x\", \"min_y\", \"max_x\", \"max_y\") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (edge_id, source, target, float(edge_data['length']),
                 cbor2.dumps(geom), bbox[0], bbox[1], bbox[2], bbox[3]),
            )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise KeyError(f"Edge {edge_id} already exists.") from exc
            raise
        self._store.mark_dirty()

    def update_edge(self, edge_data: Dict[str, Any]) -> None:
        self._validate_edge_data(edge_data)
        edge_id = int(edge_data['id'])
        _ = self.get_edge(edge_id)
        source = int(edge_data['source'])
        target = int(edge_data['target'])
        geom = self._normalize_linestring(edge_data, self.get_node)
        bbox = self._edge_bbox_from_geom(geom)
        self._conn.execute(
            f"UPDATE {self._tedges} SET \"source\" = ?, \"target\" = ?, \"length\" = ?, \"geom\" = ?, "
            f"\"min_x\" = ?, \"min_y\" = ?, \"max_x\" = ?, \"max_y\" = ? WHERE \"id\" = ?",
            (source, target, float(edge_data['length']), cbor2.dumps(geom),
             bbox[0], bbox[1], bbox[2], bbox[3], edge_id),
        )
        self._store.mark_dirty()

    def remove_edge(self, edge_id: int) -> None:
        self._conn.execute(f"DELETE FROM {self._tedges} WHERE \"id\" = ?", (edge_id,))
        self._store.mark_dirty()

    def get_edge(self, edge_id: int) -> OSMEdge:
        self._flush()
        cursor = self._conn.cursor()
        cursor.execute(
            f"SELECT \"id\", \"source\", \"target\", \"length\", \"geom\" FROM {self._tedges} WHERE \"id\" = ?",
            (edge_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Edge {edge_id} does not exist.")
        geom = tuple(tuple(c) for c in cbor2.loads(row[4]))
        return _OSMEdge(row[0], row[1], row[2], row[3], geom)

    @overload
    def get_edges(self) -> Iterator[int]: ...
    @overload
    def get_edges(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_edges(self, d: float = -1.0, x: float = 0.0, y: float = 0.0) -> Iterator[int]:
        self._flush()
        cursor = self._conn.cursor()
        if d >= 0:
            x_min, x_max = x - d, x + d
            y_min, y_max = y - d, y + d
            cursor.execute(
                f"SELECT \"id\" FROM {self._tedges} "
                f"WHERE NOT (\"max_x\" < ? OR \"min_x\" > ? OR \"max_y\" < ? OR \"min_y\" > ?)",
                (x_min, x_max, y_min, y_max),
            )
        else:
            cursor.execute(f"SELECT \"id\" FROM {self._tedges}")
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]

    def get_neighbors(self, node_id: int) -> Iterator[int]:
        _ = self.get_node(node_id)
        cursor = self._conn.cursor()
        cursor.execute(f"SELECT \"target\" FROM {self._tedges} WHERE \"source\" = ?", (node_id,))
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]

    # ---- polygons --------------------------------------------------------

    def add_polygon(
        self,
        polygon_id: int,
        coords: Any,
        height: float = DEFAULT_BUILDING_HEIGHT,
        base: float = 0.0,
        category: str = "building",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        if height <= 0:
            raise ValueError("Polygon height must be positive.")
        normalized = _normalize_polygon_coords(coords)
        bbox = _polygon_bbox(normalized)
        try:
            self._conn.execute(
                f"INSERT INTO {self._tpolys} (\"id\", \"coords\", \"height\", \"base\", \"category\", "
                f"\"attributes\", \"min_x\", \"min_y\", \"max_x\", \"max_y\") "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (int(polygon_id), cbor2.dumps(normalized), float(height), float(base),
                 str(category), cbor2.dumps(dict(attributes or {})),
                 bbox[0], bbox[1], bbox[2], bbox[3]),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Polygon {polygon_id} already exists.") from exc
        self._store.mark_dirty()

    def get_polygon(self, polygon_id: int) -> Dict[str, Any]:
        self._flush()
        cursor = self._conn.cursor()
        cursor.execute(
            f"SELECT \"id\", \"coords\", \"height\", \"base\", \"category\", \"attributes\" "
            f"FROM {self._tpolys} WHERE \"id\" = ?",
            (polygon_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Polygon {polygon_id} does not exist.")
        return {
            'id': row[0],
            'coords': [tuple(c) for c in cbor2.loads(row[1])],
            'height': row[2],
            'base': row[3],
            'category': row[4],
            'attributes': dict(cbor2.loads(row[5]) or {}),
        }

    @overload
    def get_polygons(self) -> Iterator[int]: ...
    @overload
    def get_polygons(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_polygons(self, d: float = -1.0, x: float = 0.0, y: float = 0.0) -> Iterator[int]:
        self._flush()
        cursor = self._conn.cursor()
        if d >= 0:
            x_min, x_max = x - d, x + d
            y_min, y_max = y - d, y + d
            cursor.execute(
                f"SELECT \"id\" FROM {self._tpolys} "
                f"WHERE NOT (\"max_x\" < ? OR \"min_x\" > ? OR \"max_y\" < ? OR \"min_y\" > ?)",
                (x_min, x_max, y_min, y_max),
            )
        else:
            cursor.execute(f"SELECT \"id\" FROM {self._tpolys}")
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]

    def remove_polygon(self, polygon_id: int) -> None:
        self._conn.execute(f"DELETE FROM {self._tpolys} WHERE \"id\" = ?", (polygon_id,))
        self._store.mark_dirty()


class GraphEngine(IGraphEngine):
    def __init__(self, ctx: IContext, engine: Enum = Engine.SQLITE):
        self.ctx = ctx
        self._engine_kind = engine
        self._tempdir: Optional[tempfile.TemporaryDirectory] = None
        ictx = getattr(self.ctx, 'ictx', None)
        if ictx is None or ictx.memory is None:
            raise RuntimeError(
                "GraphEngine requires a memory engine. Initialise the context "
                "via gamms.create_context()."
            )
        memory_engine = ictx.memory
        if engine == Engine.MEMORY:
            store = memory_engine.create_store(StoreType.MEMORY, GRAPH_STORE_NAME)
            self._graph: _GraphBase = Graph(cast(MemoryStore, store))
        elif engine == Engine.SQLITE:
            self._tempdir = tempfile.TemporaryDirectory(dir='.')
            db_path = PathLike(os.path.join(self._tempdir.name, 'graph.db'))
            store = memory_engine.create_store(StoreType.DATABASE, GRAPH_STORE_NAME, db_path)
            self._graph = SqliteGraph(cast(SqliteStore, store))
        else:
            raise ValueError(f"Unsupported engine type: {engine}")

    @property
    def graph(self) -> IGraph:
        return self._graph

    def attach_networkx_graph(self, G: nx.Graph) -> IGraph:
        try:
            self._graph.attach_networkx_graph(G)
        except Exception as exc:
            raise ValueError(f"Failed to attach NetworkX graph: {exc}") from exc
        return self._graph

    def add_polygon(
        self,
        polygon_id: int,
        coords: Any,
        height: float = DEFAULT_BUILDING_HEIGHT,
        base: float = 0.0,
        category: str = "building",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._graph.add_polygon(polygon_id, coords, height=height, base=base,
                                category=category, attributes=attributes)

    def get_polygon(self, polygon_id: int) -> Dict[str, Any]:
        return self._graph.get_polygon(polygon_id)

    @overload
    def get_polygons(self) -> Iterator[int]: ...
    @overload
    def get_polygons(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_polygons(self, d: float = -1.0, x: float = 0.0, y: float = 0.0) -> Iterator[int]:
        if d < 0:
            return self._graph.get_polygons()
        return self._graph.get_polygons(d, x, y)

    def remove_polygon(self, polygon_id: int) -> None:
        self._graph.remove_polygon(polygon_id)

    def load(self, path: str) -> IGraph:
        if hasattr(self._graph, 'load'):
            self._graph.load(path)  # type: ignore[attr-defined]
        else:
            raise RuntimeError("load() is only supported by the in-memory Graph backend.")
        return self._graph

    def terminate(self) -> None:
        try:
            close = getattr(getattr(self._graph, '_store', None), 'close', None)
            if callable(close):
                close()
        except Exception:
            pass
        if self._tempdir is not None:
            try:
                self._tempdir.cleanup()
            except Exception:
                pass
            self._tempdir = None
