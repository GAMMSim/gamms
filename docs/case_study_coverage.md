
# Case Study: Implementing a Coverage Simulation in GAMMS

## Introduction

This case study explores the implementation of a coverage simulation using the GAMMS framework. Agents are tasked with patrolling a graph-based environment to ensure all nodes are visited at least once. The simulation terminates when all nodes have been visited.

## Simulation Overview

- **Objective:** Deploy multiple agents to patrol a specified area, ensuring that every point (node) within the area is visited.
- **Environment:** A graph-based representation of the area, where nodes represent specific locations and edges denote possible paths between them.
- **Agents:** Autonomous units capable of navigating the graph, equipped with sensors to detect their surroundings and other agents.

## Configuration (`config.py`)

The `config.py` file defines the configuration settings for the coverage simulation, including visualization settings, graph configuration, sensor definitions, and agent configurations.

```python
import gamms

# Visualization Engine
vis_engine = gamms.visual.Engine.PYGAME

# Graph Configuration
location = "Sample Area"
resolution = 100.0
graph_path = 'graph.pkl'

# Sensor Configuration
sensor_config = {
    'neigh': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'map': {'type': gamms.sensor.SensorType.MAP},
    'agent': {'type': gamms.sensor.SensorType.AGENT},
}

# Agent Configuration
agent_config = {
    f'agent_{i}': {
        'meta': {'team': 0},
        'sensors': ['neigh', 'map', 'agent'],
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
        'color': 'blue',
        'size': 8,
    } for i in range(5)
}
```

## Agent Strategy (`coverage_strategy.py`)

The `coverage_strategy.py` file defines the strategy logic for agents to ensure area coverage. Agents move to unvisited neighboring nodes to maximize coverage.

```python
import random
from gamms import sensor

def strategy(state):
    sensor_data = state['sensor']
    unvisited_neighbors = []

    # Check neighbors and track unvisited ones
    for (type, data) in sensor_data.values():
        if type == sensor.SensorType.NEIGHBOR:
            for neighbor in data:
                # Use state['memory'] to identify unvisited nodes
                if not state['memory'].get(neighbor, False):
                    unvisited_neighbors.append(neighbor)
            break

    if unvisited_neighbors:
        next_node = random.choice(unvisited_neighbors)
        state['memory'][next_node] = True  # Mark as visited
        state['action'] = next_node
    else:
        # If all neighbors are visited, move to a random neighbor
        state['action'] = random.choice(data)


def map_strategy(agent_config):
    strategies = {}
    for name in agent_config.keys():
        strategies[name] = strategy
    return strategies
```

## Game Execution (`game.py`)

The simulation logic has been updated to include a termination condition based on node coverage. The simulation ends when all nodes in the graph are visited.

```python
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

        # Initialize memory in the agent's state if it doesn't exist
        if 'memory' not in state:
            state['memory'] = {}

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
```