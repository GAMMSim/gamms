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
from gamms.typing.artist import IArtist
from gamms.typing.context import IContext
from gamms.VisualizationEngine import Color, Shape
from gamms.VisualizationEngine.artist import Artist
from gamms.VisualizationEngine.default_drawers import render_rectangle

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
def custom_circle_drawer(ctx: IContext, data: dict):
    """
    In the custom artist drawer, you will get the context and the artist you set.
    You can then use the artist to get the data you set in the artist, and use the context to render the artist.

    Args:
        ctx (IContext): The context you set when creating the artist.
        data (dict): The data you set in the artist.
    """
    x = data.get('x')
    y = data.get('y')
    radius = data.get('radius')
    color = data.get('color')
    ctx.visual.render_circle(x, y, radius, color)

# Special nodes
n1 = ctx.graph.graph.get_node(0)
n2 = ctx.graph.graph.get_node(1)

# You can create the artist directly
custom_artist1 = Artist(ctx, Shape.Circle, 5)
# Alternatively, you can use the custom drawer
# custom_artist1 = Artist(ctx, custom_circle_drawer, 5)
custom_artist1.data['x'] = n1.x
custom_artist1.data['y'] = n1.y
custom_artist1.data['radius'] = 10
custom_artist1.data['color'] = Color.Red
ctx.visual.add_artist('special_node1', custom_artist1)

# Alternatively, you can use dict to set the data
# node_data = {}
# node_data['x'] = n1.x
# node_data['y'] = n1.y
# node_data['radius'] = 10.0
# node_data['color'] = (255, 0, 0)
# node_data['shape'] = Shape.Circle
# # Alternatively, you can use the custom drawer
# # node_data['drawer'] = custom_circle_drawer
# node_data['layer'] = 5
# custom_artist1 = ctx.visual.add_artist('special_node_test', node_data)

custom_artist2 = Artist(ctx, Shape.Rectangle)
# Alternatively, you can use the builtin drawer directly
# custom_artist2 = Artist(ctx, render_rectangle)
custom_artist2.data['x'] = n2.x
custom_artist2.data['y'] = n2.y
custom_artist2.data['width'] = 10
custom_artist2.data['height'] = 10
custom_artist2.data['color'] = Color.Cyan
ctx.visual.add_artist('special_node2', custom_artist2)

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
            state = agent.get_state()
            agent.strategy(state)
        else:
            state = agent.get_state()
            node = ctx.visual.human_input(agent.name, state)
            state['action'] = node

    for agent in ctx.agent.create_iter():
        agent.set_state()

    #valid_step(ctx)
    #agent_reset(ctx)
    if turn_count % 2 == 0:
        custom_artist1.data['x'] = n1.x
        custom_artist1.data['y'] = n1.y
        custom_artist2.data['x'] = n2.x
        custom_artist2.data['y'] = n2.y
        # node_data['x'] = n1.x
        # node_data['y'] = n1.y
        # Layer must be set in the artist
        custom_artist1.set_layer(5)
    else:
        custom_artist1.data['x'] = n2.x
        custom_artist1.data['y'] = n2.y
        custom_artist2.data['x'] = n1.x
        custom_artist2.data['y'] = n1.y
        # node_data['x'] = n2.x
        # node_data['y'] = n2.y
        # Layer must be set in the artist
        custom_artist1.set_layer(50)

    ctx.visual.simulate()

    # ctx.save_frame()
    rule_terminate(ctx)