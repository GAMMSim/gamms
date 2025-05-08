from config import location, graph_path, resolution
import gamms, gamms.osm
import pickle
# Create a graph

G = gamms.osm.create_osm_graph(location, resolution=resolution)

# Save the graph
with open(graph_path, 'wb') as f:
    pickle.dump(G, f)