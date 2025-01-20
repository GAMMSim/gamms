import pickle 
import gamms
from gamms.typing.recorder import OpCodes as op
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

    if opcode == op.SENSOR_CREATE:
        # Re-create sensor
        ctx.sensor.create_sensor(
            data['id'],
            data['type'],
            **data["kwargs"]
        )
    elif opcode == op.AGENT_CREATE:
        agent = ctx.agent.create_agent(
            name=data["name"],
            replay=True,
            **data["kwargs"]
        )
        agent_map[data["name"]] = agent
        print(f"Agent {data['name']} created")
        ctx.visual.set_agent_visual(name=data["name"], **agent_vis_config[data["name"]])

    elif opcode == op.AGENT_CURRENT_NODE:
        print(data)
        agent_name = data["agent_name"]
        node_id = data["node_id"]
        agent_map[agent_name].current_node_id = node_id

    elif opcode == op.AGENT_PREV_NODE:
        print(data)
        agent_name = data["agent_name"]
        node_id = data["node_id"]
        agent_map[agent_name].prev_node_id = node_id
    
    ctx.visual.simulate()
    # time.sleep(0.25)

#ctx.visual.simulate()
# print("Replay complete. All agent movements have been restored.")
