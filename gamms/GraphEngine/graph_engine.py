import networkx as nx
from typing import Dict, Any, List
from gamms.typing.graph_engine import Node, OSMEdge, IGraph, IGraphEngine
import pickle
from shapely.geometry import LineString
from shapely import wkb


class Graph(IGraph):
    def __init__(self, ctx=None):
        self._ctx = ctx
        # ensure memory engine has SQLite connection
        conn = self._ctx.memory.conn

        self.node_store = self._ctx.memory.create_store(
            store_type=None,  # unused for table stores
            name="nodes",
            schema={"id": "INTEGER", "x": "REAL", "y": "REAL"},
            primary_key="id"
        )
        self.edge_store = self._ctx.memory.create_store(
            store_type=None,
            name="edges",
            schema={
                "id": "INTEGER",
                "source": "INTEGER",
                "target": "INTEGER",
                "length": "REAL",
                "geom": "BLOB"
            },
            primary_key="id"
        )

    def add_node(self, node_data: Dict[str, Any]) -> None:
        # persist node
        self.node_store.save({
            "id": node_data["id"],
            "x": node_data["x"],
            "y": node_data["y"]
        })

    def get_node(self, node_id: int) -> Node:
        row = self.node_store.load(node_id)
        return Node(id=row["id"], x=row["x"], y=row["y"])

    def get_nodes(self) -> List[Node]:
        cur = self._ctx.memory.conn.execute("SELECT id FROM nodes")
        return [self.get_node(r[0]) for r in cur.fetchall()]

    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        # build or validate LineString
        linestring = edge_data.get("linestring")
        if linestring is None:
            source_node = self.get_node(edge_data['source'])
            target_node = self.get_node(edge_data['target'])
            linestring = LineString([(source_node.x, source_node.y), (target_node.x, target_node.y)])
        elif not isinstance(linestring, LineString):
            linestring = LineString(linestring)
        if linestring.is_empty:
            raise ValueError(f"Invalid linestring: {linestring}")
        # serialize geometry to WKB
        geom_wkb = wkb.dumps(linestring)
        # persist edge
        self.edge_store.save({
            "id": edge_data["id"],
            "source": edge_data["source"],
            "target": edge_data["target"],
            "length": edge_data["length"],
            "geom": geom_wkb
        })

    def get_edge(self, edge_id: int) -> OSMEdge:
        row = self.edge_store.load(edge_id)
        linestring = wkb.loads(row["geom"])
        return OSMEdge(
            id=row["id"],
            source=row["source"],
            target=row["target"],
            length=row["length"],
            linestring=linestring
        )

    def get_edges(self) -> List[OSMEdge]:
        cur = self._ctx.memory.conn.execute("SELECT id FROM edges")
        return [self.get_edge(r[0]) for r in cur.fetchall()]

    def update_node(self, node_data: Dict[str, Any]) -> None:
        existing = self.node_store.load(node_data["id"])
        updated = {"id": existing["id"],
                   "x": node_data.get("x", existing["x"]),
                   "y": node_data.get("y", existing["y"]) }
        self.node_store.save(updated)

    def update_edge(self, edge_data: Dict[str, Any]) -> None:
        existing = self.edge_store.load(edge_data["id"])
        # preserve or update geometry
        if "linestring" in edge_data:
            ls = edge_data["linestring"]
            if ls is None:
                source_node = self.get_node(edge_data['source'])
                target_node = self.get_node(edge_data['target'])
                ls = LineString([(source_node.x, source_node.y), (target_node.x, target_node.y)])
            elif not isinstance(ls, LineString):
                ls = LineString(ls)
            if ls.is_empty:
                raise ValueError(f"Invalid linestring: {ls}")
            geom_wkb = wkb.dumps(ls)
        else:
            geom_wkb = existing["geom"]
        updated = {
            "id": existing["id"],
            "source": edge_data.get("source", existing["source"]),
            "target": edge_data.get("target", existing["target"]),
            "length": edge_data.get("length", existing["length"]),
            "geom": geom_wkb
        }
        self.edge_store.save(updated)

    def remove_node(self, node_id: int) -> None:
        self._ctx.memory.conn.execute(
            "DELETE FROM edges WHERE source=? OR target=?", (node_id, node_id)
        )
        self._ctx.memory.conn.commit()
        self.node_store.delete(node_id)

    def remove_edge(self, edge_id: int) -> None:
        self.edge_store.delete(edge_id)

    def attach_networkx_graph(self, G: nx.Graph) -> None:
        for n, data in G.nodes(data=True):
            self.add_node({"id": n, "x": data.get("x", 0.0), "y": data.get("y", 0.0)})
        for u, v, data in G.edges(data=True):
            self.add_edge({
                "id": data.get("id", hash((u, v))),
                "source": u,
                "target": v,
                "length": data.get("length", 0.0),
                "linestring": data.get("linestring")
            })
    
            
    def save(self, path: str) -> None:
        data = {"nodes": self.get_nodes(), "edges": self.get_edges()}
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            data = pickle.load(f)
        for node in data["nodes"]:
            self.add_node({"id": node.id, "x": node.x, "y": node.y})
        for edge in data["edges"]:
            self.add_edge({
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "length": edge.length,
                "linestring": edge.linestring
            })


class GraphEngine(IGraphEngine):
    def __init__(self, ctx = None):
        self.ctx = ctx
        self._graph = Graph(ctx=ctx, db_path=None)
    
    @property
    def graph(self) -> IGraph:
        return self._graph
    
    def attach_networkx_graph(self, G: nx.Graph) -> IGraph:
        """
        Attaches a NetworkX graph to the Graph object.
        """
        self.graph.attach_networkx_graph(G)
        return self.graph

    def load(self, path: str) -> IGraph:
        """
        Loads a graph from a file.
        """
        self.graph.load(path)
        return self.graph
    
    def terminate(self):
        return
