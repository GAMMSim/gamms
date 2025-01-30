import networkx as nx
from typing import Dict, Any
from gamms.typing.graph_engine import Node, OSMEdge, IGraph, IGraphEngine
from gamms.osm import create_osm_graph
import pickle
from shapely.geometry import LineString

class Graph(IGraph):
    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[int, OSMEdge] = {}
    
    def get_edge(self, edge_id):
        return self.edges[edge_id]

    def get_edges(self):
        return self.edges
    
    def get_node(self, node_id):
        return self.nodes[node_id]

    def get_nodes(self):
        return self.nodes
    
    def add_node(self, node_data: Dict[str, Any]) -> None:
        if node_data['id'] in self.nodes:
            raise KeyError(f"Node {node_data['id']} already exists.")
        
        node = Node(id=node_data['id'], x=node_data['x'], y=node_data['y'])
        self.nodes[node_data['id']] = node
    
    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        if edge_data['id'] in self.edges:
            raise KeyError(f"Edge {edge_data['id']} already exists.")
        
        edge = OSMEdge(
            id = edge_data['id'],
            source=edge_data['source'],
            target=edge_data['target'],
            length=edge_data['length'],
            linestring=edge_data.get('linestring', None)
        )
        
        #Remap ID to be 64 Bit
        edge.id = (edge.source << 32) + edge.target

        #print("(key, id): ",(edge.id, edge_data['id']))
        #print("(edge.source, edge.target): ",(edge.source, edge.target))
        #print("(edge.length): ",(edge.length))
        
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

    def remove_edge(self, node_id) -> None:
        if node_id not in self.edges:
            raise KeyError(f"Edge {node_id} does not exist. Use add_edge to create it.")
        del self.edges[id]
    
    def attach_networkx_graph(self, G: nx.Graph) -> None:
        for node, data in G.nodes(data=True):
            node_data = {
                'id': node,
                'x': data.get('x', 0.0),
                'y': data.get('y', 0.0)
            }
            self.add_node(node_data)
            
        for u, v, key, data in G.edges(data=True, keys=True):
            linestring = data.get('linestring', None)
            if key == 1:
                u, v = v, u
                linestring = LineString(linestring.coords[::-1])

            edge_data = {
                'id': data.get('id', -1),
                'source': u,
                'target': v,
                'length': data.get('length', 0.0),
                'linestring': linestring
            }
            self.add_edge(edge_data)
            
    def visualize(self) -> None:
        # A debug function to visualize the graph
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        from shapely.geometry import LineString

        fig, ax = plt.subplots(figsize=(12, 12))

        # Draw nodes
        node_x = [node.x for node in self.nodes.values()]
        node_y = [node.y for node in self.nodes.values()]
        ax.scatter(node_x, node_y, s=10, c='blue', label='Nodes')

        # Prepare edge lines
        edge_lines = []
        for edge in self.edges.values():
            if edge.linestring and isinstance(edge.linestring, LineString):
                # Use the LineString geometry if available
                x, y = edge.linestring.xy
                edge_lines.append(list(zip(x, y)))
            else:
                # Fallback to a straight line between source and target nodes
                source_node = self.get_node(edge.source)
                target_node = self.get_node(edge.target)
                edge_lines.append([(source_node.x, source_node.y), (target_node.x, target_node.y)])

        # Create a LineCollection from the edge lines
        lc = LineCollection(edge_lines, colors='gray', linewidths=1, alpha=0.7, label='Edges')
        ax.add_collection(lc)

        # Set plot titles and labels
        ax.set_title('Graph Visualization with LineString Geometries')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')

        # Set equal scaling
        ax.set_aspect('equal', adjustable='datalim')

        # Add legend
        ax.legend()

        # Show grid
        ax.grid(True)

        # Display the plot
        plt.show()
    
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


class GraphEngine(IGraphEngine):
    def __init__(self, ctx = None):
        self.ctx = ctx
        self._graph = Graph()
    
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