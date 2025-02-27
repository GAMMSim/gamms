import gamms
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config
)
import blue_strategy
import red_strategy

import pickle

ctx = gamms.create_context(vis_engine=vis_engine)

# Load the graph
with open(graph_path, 'rb') as f:
    G = pickle.load(f)

ctx.graph.attach_networkx_graph(G)

# Create the sensors
for name, sensor in sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor.get('args', {}))


# Create the agents
for name, agent in agent_config.items():
    ctx.agent.create_agent(name, **agent)

# Create the strategies
strategies = {}

# Blue is human so do not set strategy
# strategies.update(blue_strategy.map_strategy(
#     {name: val for name, val in agent_config.items() if val['meta']['team'] == 0}
# ))

strategies.update(red_strategy.map_strategy(
    {name: val for name, val in agent_config.items() if val['meta']['team'] == 1}
))

# Set the strategies
for agent in ctx.agent.create_iter():
    agent.register_strategy(strategies.get(agent.name, None))

#  # Set visualization configurations
ctx.visual.set_graph_visual(**graph_vis_config)

# Set agent visualization configurations

for name, config in agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **config)


# Example of a custom drawer
def custom_circle_drawer(ctx, data):
    gamms.visual.render_manager.RenderManager.render_circle(ctx, data['x'], data['y'], data['scale'], (0, 0, 255))

# Special nodes
n1 = ctx.graph.graph.get_node(0)
n2 = ctx.graph.graph.get_node(1)
data = {}
data['x'] = n1.x
data['y'] = n1.y
data['scale'] = 10.0
data['color'] = (255, 0, 0)
data['drawer'] = custom_circle_drawer

ctx.visual.add_artist('special_node', data)

turn_count = 0
# Rules for the game
def rule_terminate(ctx):
    global turn_count
    turn_count += 1
    if turn_count > 100:
        ctx.terminate()

def agent_reset(ctx):
    blue_agent_pos = {}
    red_agent_pos = {}
    for agent in ctx.agent.create_iter():
        if agent.meta['team'] == 0:
            blue_agent_pos[agent.name] = agent.current_node_id
        else:
            red_agent_pos[agent.name] = agent.current_node_id
    for blue_agent in blue_agent_pos:
        for red_agent in red_agent_pos:
            if blue_agent_pos[blue_agent] == red_agent_pos[red_agent]:
                ctx.agent.get_agent(red_agent).current_node_id = 0

def valid_step(ctx):
    for agent in ctx.agent.create_iter():
        state = agent.get_state()
        sensor_name = agent_config[agent.name]['sensors'][0]
        if agent.current_node_id not in state[sensor_name]:
            agent.current_node_id = agent.prev_node_id

# Run the game
while not ctx.is_terminated():
    for agent in ctx.agent.create_iter():
        if agent.strategy is not None:
            agent.step()
        else:
            state = agent.get_state()
            node = ctx.visual.human_input(agent.name, state)
            state['action'] = node
            agent.set_state()

    #valid_step(ctx)
    #agent_reset(ctx)
    if turn_count % 2 == 0:
        data['x'] = n1.x
        data['y'] = n1.y
    else:
        data['x'] = n2.x
        data['y'] = n2.y
    ctx.visual.simulate()

    # ctx.save_frame()
    rule_terminate(ctx)