import gamms
from gamms.VisualizationEngine.artist import Artist
from gamms.VisualizationEngine.default_drawers import render_circle
from gamms.VisualizationEngine import Color
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config,
    sensor_vis_config,
)
import blue_strategy
import red_strategy

import pickle

ctx = gamms.create_context(vis_engine=vis_engine)

ctx.record.start(path="recording")

# Load the graph
with open(graph_path, 'rb') as f:
    G = pickle.load(f)

ctx.graph.attach_networkx_graph(G)

# Create the sensors
for name, sensor in sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor)


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

# Register the strategies
for agent in ctx.agent.create_iter():
    agent.register_strategy(strategies.get(agent.name, None))

# Set visualization configurations
graph_artist = ctx.visual.set_graph_visual(**graph_vis_config)

# for fog of war
graph_artist.set_visible(False)

# Set agent visualization configurations
agent_artists = {}
for name, config in agent_vis_config.items():
    artist = ctx.visual.set_agent_visual(name, **config)
    artist.set_visible(False)
    agent_artists[name] = artist


sensor_artists = {}
for name, config in sensor_vis_config.items():
    artist = ctx.visual.set_sensor_visual(name, **config)
    artist.set_visible(False)
    sensor_artists[name] = artist


turn_count = 0
# Rules for the game
def rule_terminate(ctx):
    global turn_count
    turn_count += 1
    if turn_count > 5:
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
        if agent.prev_node_id not in state['sensor'][sensor_name]:
            agent.current_node_id = agent.prev_node_id

# Run the game
while not ctx.is_terminated():
    for agent in ctx.agent.create_iter():
        agent_artists[agent.name].set_visible(True)
        for sensor in agent._sensor_list.values():
            sensor_artists[sensor.sensor_id].set_visible(True)
    
        if agent.strategy is not None:
            state = agent.get_state()
            agent.strategy(state)
        else:
            state = agent.get_state()
            node = ctx.visual.human_input(agent.name, state)
            state['action'] = node


        agent_artists[agent.name].set_visible(False)
        for sensor in agent._sensor_list.values():
            sensor_artists[sensor.sensor_id].set_visible(False)
            
    for agent in ctx.agent.create_iter():
        agent.set_state()

    # valid_step(ctx)
    agent_reset(ctx)
    graph_artist.set_visible(True)
    for agent in ctx.agent.create_iter():
        agent_artists[agent.name].set_visible(True)
    ctx.visual.simulate()
    for agent in ctx.agent.create_iter():
        agent_artists[agent.name].set_visible(False)
    graph_artist.set_visible(False)
    rule_terminate(ctx)
