import networkx as nx
from typing import Dict, Any, Iterator, Mapping, Tuple, cast, Union, Set, overload
from enum import Enum
from gamms.typing import Node, OSMEdge, IGraph, IGraphEngine, IContext, ObsFace
from gamms.typing.graph_engine import Engine
from gamms.typing.memory_engine import StoreType
from gamms.MemoryEngine.memory_engine import MemoryStore, SqliteStore, PathLike
from shapely.geometry import LineString

from dataclasses import dataclass

import tempfile

_Node = dataclass()(Node)
_OSMEdge = dataclass()(OSMEdge)
_ObsFace = dataclass()(ObsFace)

class Graph(IGraph):
    def __init__(self, store: MemoryStore):
        self.store = store
        self.store.create_map(
            "nodes",
            primary_key="id",
            schema={"id": int, "x": float, "y": float}
        )
        self.store.create_map(
            "edges",
            primary_key="id",
            schema={"id": int, "source": int, "target": int, "length": float, "linestring": LineString}
        )
        self._adjacency: Dict[int, Set[int]] = {}

    def get_edge(self, edge_id: int) -> OSMEdge:
        return _OSMEdge(**self.store.get_data("edges", edge_id))

    @overload
    def get_edges(self) -> Iterator[int]: ...
    @overload
    def get_edges(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_edges(self, d: float = -1.0, x: float = 0, y: float = 0) -> Iterator[int]:
        return iter(self.store.query_keys("edges"))
    
    def get_node(self, node_id: int) -> Node:
        return _Node(**self.store.get_data("nodes", node_id))
    
    @overload
    def get_nodes(self) -> Iterator[int]: ...
    @overload
    def get_nodes(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_nodes(self, d: float = -1.0, x: float = 0, y: float = 0) -> Iterator[int]:
        return iter(self.store.query_keys("nodes"))

    def add_node(self, node_data: Dict[str, Any]) -> None:
        self.store.insert_data("nodes", node_data)
        self._adjacency[node_data['id']] = set()
    
    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        linestring = edge_data.get('linestring', None)
        source_node = self.get_node(edge_data['source'])
        target_node = self.get_node(edge_data['target'])
        if linestring is None:
            # Create a LineString from the source and target node coordinates
            linestring = LineString([(source_node.x, source_node.y), (target_node.x, target_node.y)])
        elif not isinstance(linestring, LineString):
            try:
                linestring = LineString(linestring)
            except Exception as e:
                raise ValueError(f"Invalid linestring data: {linestring}") from e
        if linestring.is_empty:
            raise ValueError(f"Invalid linestring: {linestring}")

        edge_data['linestring'] = linestring

        self.store.insert_data("edges", edge_data)
        self._adjacency[edge_data['source']].add(edge_data['target'])

    def update_node(self, node_data: Dict[str, Any]) -> None:
        self.store.update_data("nodes", node_data)
    
    def update_edge(self, edge_data: Dict[str, Any]) -> None:
        existing_edge = self.get_edge(edge_data['id'])
        self._adjacency[existing_edge.source].discard(existing_edge.target)
        self.store.update_data("edges", edge_data)
        self._adjacency[edge_data['source']].add(edge_data['target'])

    def remove_node(self, node_id: int) -> None:
        if node_id not in self._adjacency:
            return
        
        edges_to_remove = []
        for edge_id in self.get_edges():
            edge = self.get_edge(edge_id)
            if edge.source == node_id or edge.target == node_id:
                edges_to_remove.append(edge_id)
        for key in edges_to_remove:
            self.store.delete_data("edges", key)
        self.store.delete_data("nodes", node_id)

        del self._adjacency[node_id]
        for neighbors in self._adjacency.values():
            neighbors.discard(node_id)

    def remove_edge(self, edge_id: int) -> None:
        edge = self.get_edge(edge_id)
        self._adjacency[edge.source].discard(edge.target)
        self.store.delete_data("edges", edge_id)
    
    def attach_networkx_graph(self, G: nx.Graph) -> None:
        for node, data in G.nodes(data=True): # type: ignore
            node = cast(int, node)
            data = cast(Dict[str, Any], data)
            node_data: Dict[str, Union[int, float]] = {
                'id': node,
                'x': data.get('x', 0.0),
                'y': data.get('y', 0.0)
            }
            self.add_node(node_data)
            
        for u, v, data in G.edges(data=True): # type: ignore
            u = cast(int, u)
            v = cast(int, v)
            data = cast(Dict[str, Any], data)
            linestring = data.get('linestring', None)
            if linestring is None:
                # Create a LineString from the source and target node coordinates
                source_node = self.get_node(u)
                target_node = self.get_node(v)
                linestring = LineString([(source_node.x, source_node.y), (target_node.x, target_node.y)])
            elif not isinstance(linestring, LineString):
                try:
                    linestring = LineString(linestring)
                except Exception as e:
                    raise ValueError(f"Invalid linestring data: {linestring}") from e
            if linestring.is_empty:
                raise ValueError(f"Invalid linestring: {linestring}")
            edge_data: Dict[str, Any] = {
                'id': data.get('id', -1),
                'source': u,
                'target': v,
                'length': data.get('length', 0.0),
                'linestring': linestring
            }
            self.add_edge(edge_data)
    

    def get_neighbors(self, node_id: int) -> Iterator[int]:
        if node_id not in self._adjacency:
            raise KeyError(f"Node {node_id} does not exist.")

        for neighbor in self._adjacency[node_id]:
            yield neighbor

class SqliteGraph(IGraph):
    def __init__(self, store: SqliteStore):
        self.store = store

        # Enable foreign key constraints and set journal mode to WAL for better concurrency
        # Also set temp_store to MEMORY for faster temporary storage
        self.store.connection().executescript(
            "PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;PRAGMA temp_store = MEMORY;"
            )

        self.store.create_map(
            "nodes",
            primary_key="id",
            schema={"id": int, "x": float, "y": float}
        )

        self.store.create_map(
            "edges",
            primary_key="id",
            schema={"id": int, "source": int, "target": int, "length": float, "linestring": LineString}
        )

        self.store.connection().execute("CREATE INDEX IF NOT EXISTS idx_nodes_xy ON nodes (x, y)")
        self.store.connection().executescript(
            """
            ALTER TABLE edges RENAME TO old_edges;
            CREATE TABLE edges (
                id INTEGER PRIMARY KEY,
                source INTEGER NOT NULL,
                target INTEGER NOT NULL,
                length REAL NOT NULL,
                linestring BLOB,
                FOREIGN KEY (source) REFERENCES nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (target) REFERENCES nodes(id) ON DELETE CASCADE
            );
            
            DROP TABLE old_edges;
            """
        )
        self.store.connection().execute("CREATE INDEX IF NOT EXISTS idx_edges_source_target ON edges (source, target)")
    
    def add_node(self, node_data: Dict[str, Any]) -> None:
        """
        Adds a node to the graph.
        """
        self.store.insert_data("nodes", node_data)

    
    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        """
        Adds an edge to the graph.
        """
        linestring = edge_data.get('linestring', None)
        source_node = self.get_node(edge_data['source'])
        target_node = self.get_node(edge_data['target'])
        if linestring is None:
            # Create a LineString from the source and target node coordinates
            linestring = LineString([(source_node.x, source_node.y), (target_node.x, target_node.y)])
        elif not isinstance(linestring, LineString):
            try:
                linestring = LineString(linestring)
            except Exception as e:
                raise ValueError(f"Invalid linestring data: {linestring}") from e
        if linestring.is_empty:
            raise ValueError(f"Invalid linestring: {linestring}")

        edge_data['linestring'] = tuple(linestring.coords)

        self.store.insert_data("edges", edge_data)
    
    def get_node(self, node_id: int) -> Node:
        """
        Retrieves a node by its ID.
        """
        return _Node(**self.store.get_data("nodes", node_id))
    
    @overload
    def get_edges(self) -> Iterator[int]: ...
    @overload
    def get_edges(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_edges(self, d: float = -1.0, x: float = 0, y: float = 0) -> Iterator[int]:
        """
        Returns an iterator over all edge IDs in the graph.
        """
        self.store.flush()  # Ensure all pending changes are written to the database
        cursor = self.store.connection().cursor()
        if d >= 0:
            x_min, x_max = x - d, x + d
            y_min, y_max = y - d, y + d
            cursor.execute("SELECT edges.id FROM edges JOIN nodes AS u ON edges.source = u.id JOIN nodes AS v ON edges.target = v.id WHERE (u.x BETWEEN ? AND ? AND u.y BETWEEN ? AND ?) OR (v.x BETWEEN ? AND ? AND v.y BETWEEN ? AND ?)",
                           (x_min, x_max, y_min, y_max, x_min, x_max, y_min, y_max))
        else:
            cursor.execute("SELECT id FROM edges")
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]
    
    def get_edge(self, edge_id: int) -> OSMEdge:
        """
        Retrieves an edge by its ID.
        """
        return _OSMEdge(**self.store.get_data("edges", edge_id))
    
    @overload
    def get_nodes(self) -> Iterator[int]: ...
    @overload
    def get_nodes(self, d: float, x: float, y: float) -> Iterator[int]: ...
    def get_nodes(self, d: float = -1.0, x: float = 0, y: float = 0) -> Iterator[int]:
        """
        Returns an iterator over all node IDs in the graph.
        """
        self.store.flush()
        cursor = self.store.cursor()
        if d >= 0:
            cursor.execute("SELECT id FROM nodes WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?", (x - d, x + d, y - d, y + d))
        else:
            cursor.execute("SELECT id FROM nodes")
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]
    
    def update_node(self, node_data: Dict[str, Any]) -> None:
        """
        Updates a node in the graph.
        """
        self.get_node(node_data['id'])  # Ensure node exists
        self.store.update_data("nodes", node_data)
    
    def update_edge(self, edge_data: Dict[str, Any]) -> None:
        """
        Updates an edge in the graph.
        """
        _ = self.get_edge(edge_data['id'])  # Ensure edge exists
        linestring = edge_data.get('linestring', None)
        if linestring is not None:
            edge_data['linestring'] = tuple(LineString(linestring).coords)
        self.store.update_data("edges", edge_data)
    
    def remove_node(self, node_id: int) -> None:
        """
        Removes a node from the graph.
        """
        self.store.delete_data("nodes", node_id)
    
    def remove_edge(self, edge_id: int) -> None:
        """
        Removes an edge from the graph.
        """
        self.store.delete_data("edges", edge_id)

    
    attach_networkx_graph = Graph.attach_networkx_graph
            
    def get_neighbors(self, node_id: int) -> Iterator[int]:
        """
        Returns an iterator over the neighbors of a given node.
        """
        _ = self.get_node(node_id)
        cursor = self.store.connection().cursor()
        cursor.execute("SELECT target FROM edges WHERE source = ?", (node_id,))
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]

class GraphEngine(IGraphEngine):
    def __init__(self, ctx: IContext, engine: Enum = Engine.SQLITE):
        if engine == Engine.MEMORY:
            self._store = ctx.ictx.memory.create_store(StoreType.MEMORY, name="graph_store")
            self._store = cast(MemoryStore, self._store)
            self._graph = Graph(self._store)
            self._store.create_map(
                "obstacle_face",
                primary_key="id",
                schema={
                    "id": int,
                    "trx": float, "try": float, "trz": float,
                    "brx": float, "bry": float, "brz": float,
                    "tlx": float, "tly": float, "tlz": float,
                    "blx": float, "bly": float, "blz": float,
                    "type": int
                }
            )
        elif engine == Engine.SQLITE:
            self._dbdir = tempfile.TemporaryDirectory(dir=".")
            path = PathLike(f"{self._dbdir.name}/graph.db")
            self._store = ctx.ictx.memory.create_store(StoreType.DATABASE, name="graph_store", path=path)
            self._store = cast(SqliteStore, self._store)
            self._graph = SqliteGraph(self._store)
            self._store.create_map(
                "obstacle_face",
                primary_key="id",
                schema={
                    "id": int,
                    "trx": float, "try": float, "trz": float,
                    "brx": float, "bry": float, "brz": float,
                    "tlx": float, "tly": float, "tlz": float,
                    "blx": float, "bly": float, "blz": float,
                    "type": int
                }
            )
            self._store.connection().execute(
                "CREATE INDEX IF NOT EXISTS idx_obstacle_face ON obstacle_face (trx, try, brx, bry, tlx, tly, blx, bly)"
            )
        else:
            raise ValueError(f"Unsupported engine type: {engine}")
        self.ctx = ctx
    
    @property
    def graph(self) -> IGraph:
        return self._graph
    
    def add_obstacle_face(
        self,
        face_id: int,
        tr: Tuple[float, float, float],
        tl: Tuple[float, float, float],
        br: Tuple[float, float, float],
        bl: Tuple[float, float, float],
        type: int
    ) -> None:
        self._store.insert_data("obstacle_face", {
            "id": face_id,
            "trx": tr[0], "try": tr[1], "trz": tr[2],
            "brx": br[0], "bry": br[1], "brz": br[2],
            "tlx": tl[0], "tly": tl[1], "tlz": tl[2],
            "blx": bl[0], "bly": bl[1], "blz": bl[2],
            "type": type
        })

    def remove_obstacle_face(self, face_id: int) -> None:
        self._store.delete_data("obstacle_face", face_id)
    
    def get_obstacle_face(self, face_id: int) -> ObsFace:
        ret = self._store.get_data("obstacle_face", face_id)
        ret = {
            'id': ret['id'],
            'tr': (ret['trx'], ret['try'], ret['trz']),
            'br': (ret['brx'], ret['bry'], ret['brz']),
            'tl': (ret['tlx'], ret['tly'], ret['tlz']),
            'bl': (ret['blx'], ret['bly'], ret['blz']),
            'type': ret['type']
        }
        return _ObsFace(**ret)

    def get_obstacle_faces(self, d: float = -1.0, x: float = 0, y: float = 0) -> Iterator[int]:
        if self._store.type == StoreType.MEMORY:
            for key in self._store.query_keys("obstacle_face"):
                if d >= 0:
                    data = self._store.get_data("obstacle_face", key)
                    if not (max(data['trx'], data['tlx'], data['brx'], data['blx']) >= x - d and
                            min(data['trx'], data['tlx'], data['brx'], data['blx']) <= x + d and
                            max(data['try'], data['tly'], data['bry'], data['bly']) >= y - d and
                            min(data['try'], data['tly'], data['bry'], data['bly']) <= y + d):
                        continue
                yield key
        elif self._store.type == StoreType.DATABASE:
            cursor = self._store.connection().cursor()
            if d >= 0:
                cursor.execute(
                    """SELECT id FROM obstacle_face WHERE (
                        MAX(tlx, trx, blx, brx) >= ?
                        AND MIN(tlx, trx, blx, brx) <= ?
                        AND MAX(tly, try, bly, bry) >= ?
                        AND MIN(tly, try, bly, bry) <= ?
                    )""",
                    (x - d, x + d, y - d, y + d)
                )
            else:
                cursor.execute("SELECT id FROM obstacle_face")
            while True:
                row = cursor.fetchone()
                if row is None:
                    break
                yield row[0]
        else:
            raise ValueError(f"Unsupported store type: {self._store.type}")

    
    def attach_networkx_graph(self, G: nx.Graph) -> IGraph:
        """
        Attaches a NetworkX graph to the Graph object.
        """
        try:
            self._graph.attach_networkx_graph(G)
        except Exception as e:
            raise ValueError(f"Failed to attach NetworkX graph: {e}") from e
        return self.graph

    def load(self, path: str) -> IGraph:
        """
        Loads a graph from a file.
        """
        self._graph.load(path)
        return self.graph
    
    def terminate(self):
        if self._store.type == StoreType.DATABASE:
            self._dbdir.cleanup()
        try:
            del self._graph
        except Exception as e:
            print(f"Error during graph termination: {e}")
        return