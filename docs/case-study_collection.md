
# Case Study: Developing a Resource Collection Game with GAMMS

## Introduction

This case study demonstrates the use of updated agent states to dynamically integrate food collection in a resource collection game. Instead of using a custom sensor, food positions and weights are added to the agent's state. Agents then strategize to move toward the nearest food based on this information.

## Game Overview

- **Objective:** Collect all resources (circles) scattered on the map. The game ends when all resources are collected.
- **Environment:** A graph-based map with nodes representing resource locations and edges representing paths.
- **Agents:** Autonomous units with the ability to sense nearby resources, navigate the map, and collect resources.

## Configuration (`config.py`)

The `config.py` file defines the configuration settings for the resource collection game, including visualization, graph configuration, sensor definitions, agent configurations, and resource placements.

```python
import gamms

# Visualization Engine
vis_engine = gamms.visual.Engine.PYGAME

# Graph Configuration
location = "Resource Island"
resolution = 100.0
graph_path = 'resource_graph.pkl'

# Sensor Configuration
sensor_config = {
    'neigh': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'map': {'type': gamms.sensor.SensorType.MAP},
}

# Agent Configuration
agent_config = {
    f'agent_{i}': {
        'meta': {'team': 0},
        'sensors': ['neigh', 'map'],
        'start_node_id': i
    } for i in range(5)  # Five agents starting at different nodes
}

# Visualization Configuration
graph_vis_config = {
    'width': 800,
    'height': 600
}

agent_vis_config = {
    f'agent_{i}': {
        'color': 'green',
        'size': 8,
    } for i in range(5)
}

# Food Configuration
food_data = [
    {'x': 0, 'scale': 10.0, 'color': (255, 0, 0)},  # Red food on node 0
    {'x': 1, 'scale': 15.0, 'color': (0, 255, 0)},  # Green food on node 1
    {'x': 2, 'scale': 12.0, 'color': (0, 0, 255)},  # Blue food on node 2
]
```

## Adding Food Information to Agent States

In the simulation loop, food positions and weights are dynamically added to the agent's state before executing their strategy.

```python
# Add food information to agent states
for agent in ctx.agent.create_iter():
    state = agent.get_state()

    # Add food positions and weights to the state
    state.update({
        "food_positions": [food['x'] for food in remaining_food],  # Node IDs of food
        "food_weights": [food['scale'] for food in remaining_food],  # Sizes or weights of food
    })

    # Execute the agent's strategy
    agent.strategy(state)

    # Set the updated state back
    agent.set_state()
```

## Agent Strategy (`resource_strategy.py`)

The agent strategy leverages the updated state to move toward the closest food item based on the shortest path distance.

```python
import random
import networkx as nx

def strategy(state):
    """Strategy for agents to move towards the closest food."""
    current_node = state['curr_pos']
    food_positions = state['food_positions']  # Node IDs of food
    food_weights = state['food_weights']  # Corresponding weights of food

    closest_food = None
    min_distance = float('inf')

    # Find the closest food item
    for food_node in food_positions:
        try:
            dist = nx.shortest_path_length(
                state['graph'], source=current_node, target=food_node
            )
            if dist < min_distance:
                min_distance = dist
                closest_food = food_node
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    # Set the action to move towards the closest food, if found
    if closest_food is not None:
        state['action'] = closest_food
    else:
        # Default to a random neighbor if no food is reachable
        neighbors = state.get('neigh', [])
        if neighbors:
            state['action'] = random.choice(neighbors)
```

## Game Execution (`game.py`)

The simulation loop integrates food state updates and terminates the game when all food is collected.

```python
import gamms
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config,
    food_data
)
import resource_strategy
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
strategies = resource_strategy.map_strategy(agent_config)

# Set the strategies
for agent in ctx.agent.create_iter():
    agent.register_strategy(strategies.get(agent.name, None))

# Set visualization configurations
ctx.visual.set_graph_visual(**graph_vis_config)

for name, config in agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **config)

# Track remaining food
remaining_food = food_data[:]

# Add food to the visualization
for food in remaining_food:
    n = ctx.graph.graph.get_node(food['x'])  # Get node for the food
    data = {
        'x': n.x,
        'y': n.y,
        'scale': food['scale'],
        'color': food['color']
    }
    ctx.visual.add_artist('food_node', data)

# Check if an agent "hits" a food node
def check_food_collection(ctx):
    global remaining_food
    for agent in ctx.agent.create_iter():
        agent_pos = agent.current_node_id
        for food in remaining_food:
            if food['x'] == agent_pos:  # Match node ID
                remaining_food.remove(food)
                print(f"Agent {agent.name} collected food at {agent_pos}")
                break

# Run the simulation
while not ctx.is_terminated():
    for agent in ctx.agent.create_iter():
        state = agent.get_state()
        state.update({
            "food_positions": [food['x'] for food in remaining_food],
            "food_weights": [food['scale'] for food in remaining_food],
        })
        agent.strategy(state)
        agent.set_state()

    # Check food collection
    check_food_collection(ctx)

    # Terminate if all food is collected
    if not remaining_food:
        print("All food collected! Terminating the game.")
        ctx.terminate()

    # Update the visualization
    ctx.visual.simulate()
```

