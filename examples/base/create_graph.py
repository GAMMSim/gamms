from config import location, graph_path, resolution
import gamms
import pickle
# Create a graph

# G = gamms.osm.create_osm_graph(location, resolution=resolution)
# print(G)
G = gamms.osm.graph_from_xml(filepath="/Users/jmalegaonkar/Desktop/gamms/examples/dummies/grid.osm", resolution=10)
print(G)
# Save the graph
with open(graph_path, 'wb') as f:
    pickle.dump(G, f)