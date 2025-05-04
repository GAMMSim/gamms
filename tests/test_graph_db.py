import pickle
# create context and record
from gamms.GraphEngine.graph_engine import Graph
import gamms

ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)

# Load a pickled networkx graph and attach
with open("graph.pkl", 'rb') as f:
    G_nx = pickle.load(f)
graph = Graph(ctx)
graph.attach_networkx_graph(G_nx)

print("Loaded nodes:", [n.id for n in graph.get_nodes()])
print("Loaded edges:", [(e.id, e.source, e.target) for e in graph.get_edges()])

graph.add_node({"id": 999, "x": 1.23, "y": 4.56})
print("New node:", graph.get_node(999))
graph.add_edge({"id": 888, "source": 999, "target": 999, "length": 0.0})
print("New edge:", graph.get_edge(888))