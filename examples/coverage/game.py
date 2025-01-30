import gamms
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config,
)
import coverage_strategy
import pickle

# Create the game context
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

# Assign strategies
strategies = coverage_strategy.map_strategy(agent_config)

# Set the strategies
for agent in ctx.agent.create_iter():
    agent.register_strategy(strategies.get(agent.name, None))

# Set visualization configurations
ctx.visual.set_graph_visual(**graph_vis_config)

for name, config in agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **config)

# Track visited nodes
visited_nodes = set()
total_nodes = len(ctx.graph.graph.nodes)  # Total number of nodes in the graph

# Run the simulation
while not ctx.is_terminated():
    for agent in ctx.agent.create_iter():
        # Update the visited nodes with the agent's current position
        visited_nodes.add(agent.current_node_id)

        state = agent.get_state()
        state['current_node'] = agent.current_node_id
        # Initialize memory in the agent's state if it doesn't exist
        if 'memory' not in state:
            state['memory'] = {'visited': set(), 'prev_node_id': None}
        


        # Execute the agent's strategy
        agent.strategy(state)

        # Set the updated state back
        agent.set_state()

    # Check if all nodes have been visited
    if len(visited_nodes) >= total_nodes:
        print("All nodes have been visited! Terminating the game.")
        ctx.terminate()

    # Simulate visualization
    ctx.visual.simulate()