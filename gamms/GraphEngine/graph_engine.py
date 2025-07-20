import networkx as nx
from typing import Dict, Any, Iterator, cast, Union
from gamms.typing import Node, OSMEdge, IGraph, IGraphEngine, IContext
import pickle
from shapely.geometry import LineString

import sqlite3

import tempfile
import cbor2

class Graph(IGraph):
    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[int, OSMEdge] = {}
    
    def get_edge(self, edge_id: int) -> OSMEdge:
        return self.edges[edge_id]

    def get_edges(self) -> Iterator[int]:
        return iter(self.edges.keys())
    
    def get_node(self, node_id: int) -> Node:
        return self.nodes[node_id]

    def get_nodes(self) -> Iterator[int]:
        return iter(self.nodes.keys())
    
    def add_node(self, node_data: Dict[str, Any]) -> None:
        if node_data['id'] in self.nodes:
            raise KeyError(f"Node {node_data['id']} already exists.")
        
        node = Node(id=node_data['id'], x=node_data['x'], y=node_data['y'])
        self.nodes[node_data['id']] = node
    
    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        if edge_data['id'] in self.edges:
            raise KeyError(f"Edge {edge_data['id']} already exists.")
        
        linestring = edge_data.get('linestring', None)
        if linestring is None:
            # Create a LineString from the source and target node coordinates
            source_node = self.get_node(edge_data['source'])
            target_node = self.get_node(edge_data['target'])
            linestring = LineString([(source_node.x, source_node.y), (target_node.x, target_node.y)])
        elif not isinstance(linestring, LineString):
            try:
                linestring = LineString(linestring)
            except Exception as e:
                raise ValueError(f"Invalid linestring data: {linestring}") from e
        if linestring.is_empty:
            raise ValueError(f"Invalid linestring: {linestring}")
        
        edge = OSMEdge(
            id = edge_data['id'],
            source=edge_data['source'],
            target=edge_data['target'],
            length=edge_data['length'],
            linestring=linestring
        )

        self.edges[edge_data['id']] = edge

    def update_node(self, node_data: Dict[str, Any]) -> None:
    
        if node_data['id'] not in self.nodes:
            raise KeyError(f"Node {node_data['id']} does not exist.")
        
        node = self.nodes[node_data['id']]
        node.x = node_data.get('x', node.x)
        node.y = node_data.get('y', node.y)
    
    def update_edge(self, edge_data: Dict[str, Any]) -> None:

        if edge_data['id'] not in self.edges:
            raise KeyError(f"Edge {edge_data['id']} does not exist. Use add_edge to create it.")
        edge = self.edges[edge_data['id']]
        edge.source = edge_data.get('source', edge.source)
        edge.target = edge_data.get('target', edge.target)
        edge.length = edge_data.get('length', edge.length)
        edge.linestring = edge_data.get('linestring', edge.linestring)

    def remove_node(self, node_id: int) -> None:
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} does not exist.")
        
        edges_to_remove = [key for key, edge in self.edges.items() if edge.source == node_id or edge.target == node_id]
        for key in edges_to_remove:
            del self.edges[key]
            print(f"Deleted edge {key} associated with node {node_id}")
        del self.nodes[node_id]

    def remove_edge(self, edge_id: int) -> None:
        if edge_id not in self.edges:
            raise KeyError(f"Edge {edge_id} does not exist.")
        
        del self.edges[edge_id]
    
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
                
    def save(self, path: str) -> None:
        """
        Saves the graph to a file.
        """
        pickle.dump({"nodes": self.nodes, "edges": self.edges}, open(path, 'wb'))
        print(f"Graph saved to {path}")

    def load(self, path: str) -> None:
        """
        Loads the graph from a file.
        """
        data = pickle.load(open(path, 'rb'))
        self.nodes = data['nodes']
        self.edges = data['edges']


class SqliteGraph(IGraph):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        # Create a random name for the SQLite database
        self._dbfile = tempfile.NamedTemporaryFile(dir="./", suffix=".sqlite")
        self._conn = sqlite3.connect(self._dbfile.name)
        self._cursor = self._conn.cursor()
        self.node_store = self._cursor.execute(
            "CREATE TABLE IF NOT EXISTS nodes (id INTEGER PRIMARY KEY, x REAL, y REAL)"
        )
        # Create index on node x,y for faster lookups
        self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_xy ON nodes (x, y)")
        self.edge_store = self._cursor.execute(
            "CREATE TABLE IF NOT EXISTS edges (id INTEGER PRIMARY KEY, source INTEGER, target INTEGER, length REAL, geom BLOB, FOREIGN KEY(source) REFERENCES nodes(id), FOREIGN KEY(target) REFERENCES nodes(id))"
        )
        # Create index on edge source,target for faster lookups
        self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source_target ON edges (source, target)")
        self._conn.commit()
        self._call_commit = False
    
    def __del__(self):
        """
        Destructor to close the database connection.
        """
        self._conn.close()
        if self._dbfile:
            try:
                self._dbfile.close()
            except Exception as e:
                print(f"Error closing temporary file: {e}")        
    
    def add_node(self, node_data: Dict[str, Any]) -> None:
        """
        Adds a node to the graph.
        """
        if 'id' not in node_data or 'x' not in node_data or 'y' not in node_data:
            raise ValueError("Node data must include 'id', 'x', and 'y'.")
        
        self._cursor.execute("INSERT INTO nodes (id, x, y) VALUES (?, ?, ?)", 
                       (node_data['id'], node_data['x'], node_data['y']))
        
        self._call_commit = True
    
    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        """
        Adds an edge to the graph.
        """
        if 'id' not in edge_data or 'source' not in edge_data or 'target' not in edge_data or 'length' not in edge_data:
            raise ValueError("Edge data must include 'id', 'source', 'target', and 'length'.")
        
        linestring = edge_data.get('linestring', None)
        if linestring is None:
            # Create a LineString from the source and target node coordinates
            source_node = self.get_node(edge_data['source'])
            target_node = self.get_node(edge_data['target'])
            linestring = ((source_node.x, source_node.y), (target_node.x, target_node.y))
        elif not isinstance(linestring, LineString):
            try:
                linestring = LineString(linestring)
                linestring = tuple(linestring.coords)
            except Exception as e:
                raise ValueError(f"Invalid linestring data: {linestring}") from e
        else:
            linestring = tuple(linestring.coords)

        self._cursor.execute("INSERT INTO edges (id, source, target, length, geom) VALUES (?, ?, ?, ?, ?)",
                       (edge_data['id'], edge_data['source'], edge_data['target'], edge_data['length'], cbor2.dumps(linestring)))

        self._call_commit = True
    
    def get_node(self, node_id: int) -> Node:
        """
        Retrieves a node by its ID.
        """
        if self._call_commit:
            self._conn.commit()
            self._call_commit = False
        cursor = self._conn.cursor()
        cursor.execute("SELECT id, x, y FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Node {node_id} does not exist.")
        
        return Node(id=row[0], x=row[1], y=row[2])
    
    def get_edges(self) -> Iterator[int]:
        """
        Returns an iterator over all edge IDs in the graph.
        """
        if self._call_commit:
            self._conn.commit()
            self._call_commit = False
        cursor = self._conn.cursor()
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
        if self._call_commit:
            self._conn.commit()
            self._call_commit = False
        cursor = self._conn.cursor()
        cursor.execute("SELECT id, source, target, length, geom FROM edges WHERE id = ?", (edge_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Edge {edge_id} does not exist.")
        
        return OSMEdge(id=row[0], source=row[1], target=row[2], length=row[3], linestring=LineString(cbor2.loads(row[4])))
    
    def get_nodes(self) -> Iterator[int]:
        """
        Returns an iterator over all node IDs in the graph.
        """
        if self._call_commit:
            self._conn.commit()
            self._call_commit = False
        cursor = self._conn.cursor()
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
        if 'id' not in node_data or 'x' not in node_data or 'y' not in node_data:
            raise ValueError("Node data must include 'id', 'x', and 'y'.")
        
        _ = self.get_node(node_data['id'])
        
        self._cursor.execute("UPDATE nodes SET x = ?, y = ? WHERE id = ?", 
                       (node_data['x'], node_data['y'], node_data['id']))
        
        self._call_commit = True
    
    def update_edge(self, edge_data: Dict[str, Any]) -> None:
        """
        Updates an edge in the graph.
        """
        if 'id' not in edge_data or 'source' not in edge_data or 'target' not in edge_data or 'length' not in edge_data:
            raise ValueError("Edge data must include 'id', 'source', 'target', and 'length'.")
        
        _ = self.get_edge(edge_data['id'])
        
        linestring = edge_data.get('linestring', None)
        if linestring is None:
            # Create a LineString from the source and target node coordinates
            source_node = self.get_node(edge_data['source'])
            target_node = self.get_node(edge_data['target'])
            linestring = ((source_node.x, source_node.y), (target_node.x, target_node.y))
        elif not isinstance(linestring, LineString):
            try:
                linestring = LineString(linestring)
                linestring = tuple(linestring.coords)
            except Exception as e:
                raise ValueError(f"Invalid linestring data: {linestring}") from e
        else:
            linestring = tuple(linestring.coords)
        
        self._cursor.execute("UPDATE edges SET source = ?, target = ?, length = ?, geom = ? WHERE id = ?",
                       (edge_data['source'], edge_data['target'], edge_data['length'], cbor2.dumps(linestring), edge_data['id']))
        
        self._call_commit = True
    
    def remove_node(self, node_id: int) -> None:
        """
        Removes a node from the graph.
        """
        self._cursor.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        
        # Remove edges associated with this node
        self._cursor.execute("DELETE FROM edges WHERE source = ? OR target = ?", (node_id, node_id))
        
        self._call_commit = True
    
    def remove_edge(self, edge_id: int) -> None:
        """
        Removes an edge from the graph.
        """
        self._cursor.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        
        self._call_commit = True

class GraphEngine(IGraphEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        self._graph = Graph()
    
    @property
    def graph(self) -> IGraph:
        return self._graph
    
    def attach_networkx_graph(self, G: nx.Graph) -> IGraph:
        """
        Attaches a NetworkX graph to the Graph object.
        """
        self._graph.attach_networkx_graph(G)
        return self.graph

    def load(self, path: str) -> IGraph:
        """
        Loads a graph from a file.
        """
        self._graph.load(path)
        return self.graph
    
    def terminate(self):
        return
