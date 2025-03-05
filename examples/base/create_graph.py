from config import location, graph_path, resolution
import gamms
import pickle
# Create a graph

# G = gamms.osm.create_osm_graph(location, resolution=resolution)
G = gamms.osm.graph_from_xml(filepath="/Users/jmalegaonkar/Desktop/gamms/examples/dummies/circle.osm", resolution=resolution)

# Save the graph
with open(graph_path, 'wb') as f:
    pickle.dump(G, f)