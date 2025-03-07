import gamms
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config
)


import pickle

ctx = gamms.create_context(vis_engine=vis_engine)

# Load the graph
with open(graph_path, 'rb') as f:
    G = pickle.load(f)

print(G)

print(type(G))
ctx.graph.attach_networkx_graph(G)
ctx.visual.set_graph_visual(**graph_vis_config)
while True: 
    ctx.visual.simulate()
