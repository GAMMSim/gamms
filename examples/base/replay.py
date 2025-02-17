import pickle 
import gamms
from gamms.recorder import _record_switch_case
from config import (
    vis_engine,
    graph_path,
    graph_vis_config,
)

ctx = gamms.create_context(vis_engine=vis_engine)
with open(graph_path, 'rb') as f:
    G = pickle.load(f)
ctx.graph.attach_networkx_graph(G)

ctx.visual.set_graph_visual(**graph_vis_config)


# Replay the recording
for _ in ctx.record.replay("recording.ggr"):
    continue
