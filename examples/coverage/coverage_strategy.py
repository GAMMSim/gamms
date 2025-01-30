import random
from gamms import sensor

import random
import networkx as nx  # Needed for shortest path calculations
from gamms import sensor

def strategy(state):
    """
    Optimized strategy: Moves towards the closest unvisited node using a prebuilt graph.
    """
    sensor_data = state['sensor']
    current_node = state['current_node']

    # Initialize memory storage if not already set
    if 'memory' not in state:
        state['memory'] = {'visited': {}, 'graph': None}

    visited_nodes = state['memory']['visited']

    # Mark current node as visited
    visited_nodes[current_node] = True

    # Check if the graph is already stored in memory
    if state['memory']['graph'] is None:
        # Extract map data and construct the graph once
        _,(nodes, edges) = sensor_data['map']  # This returns (nodes, edges) from MapSensor
        G = nx.Graph()
        for node_id in nodes:
            G.add_node(node_id)
        for edge in edges.values():
            G.add_edge(edge.source, edge.target)
        
        # Store the prebuilt graph in memory
        state['memory']['graph'] = G
    else:
        G = state['memory']['graph']  # Retrieve prebuilt graph

    # Get current agent positions from AgentSensor
    type_ , agent_positions = sensor_data['agent']  # Dictionary of {agent_name: node_id}
    occupied_nodes = set(agent_positions.values())  # Nodes currently occupied by agents

    # Identify unvisited neighboring nodes
    unvisited_neighbors = []
    for (sensor_type, neighbors) in sensor_data.values():
        if sensor_type == sensor.SensorType.NEIGHBOR:
            for neighbor in neighbors:
                if neighbor not in visited_nodes and neighbor not in occupied_nodes:
                    unvisited_neighbors.append(neighbor)
            break

    if unvisited_neighbors:
        # Move to the closest unvisited neighbor that isn't occupied
        next_node = min(unvisited_neighbors, key=lambda node: nx.shortest_path_length(G, current_node, node))
    else:
        # Perform a broader search for the nearest unvisited node in the graph
        unvisited_nodes = [node for node in G.nodes if node not in visited_nodes and node not in occupied_nodes]

        if unvisited_nodes:
            try:
                # Find the nearest unvisited node using shortest path
                next_node = min(unvisited_nodes, key=lambda node: nx.shortest_path_length(G, current_node, node))
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                # If no valid path exists, move to a random neighbor as a fallback
                next_node = random.choice(list(G.neighbors(current_node)))
        else:
            # If all nodes are visited, introduce small chance for random movement to break loops
            if random.random() < 0.2:  # 20% chance to move randomly
                next_node = random.choice(list(G.neighbors(current_node)))
            else:
                next_node = current_node  # Stay in place

    # Update state and move to the next node
    visited_nodes[next_node] = True
    state['action'] = next_node


def map_strategy(agent_config):
    strategies = {}
    for name in agent_config.keys():
        strategies[name] = strategy
    return strategies