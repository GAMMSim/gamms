import gamms
import gamms.osm
from gamms.VisualizationEngine import Color


# Create Manhattan graph
print("Creating Manhattan graph...")
G = gamms.osm.create_osm_graph("Central Park, Manhattan, New York City, New York, USA", resolution=100.0)
print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

# Create gamms context and visualize
print("Starting visualization...")
ctx = gamms.create_context(vis_engine=gamms.visual.Engine.PYGAME)
ctx.graph.attach_networkx_graph(G)
ctx.visual.set_graph_visual(node_color=Color.Blue, edge_color=Color.Red, node_size=16)


# Run visualization loop
while not ctx.is_terminated():
    ctx.visual.simulate()