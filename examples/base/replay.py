import pickle 
import gamms
from gamms.typing.opcodes import OpCodes as op
from gamms.recorder import _record_switch_case
import time
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config
)

ctx = gamms.create_context(vis_engine=vis_engine)
with open(graph_path, 'rb') as f:
    G = pickle.load(f)
ctx.graph.attach_networkx_graph(G)

ctx.visual.set_graph_visual(**graph_vis_config)


# 3) Load the recorded events
with open('recording.pkl', 'rb') as f:
    recorded_data = pickle.load(f)


agent_map = {}

for event in recorded_data:
    opcode = event['opCode']
    data = event['data']
    _record_switch_case(ctx, opcode, data)