import random

nodes = {}

current_opposite_agents = {}
capturable_nodes = set()
self_territory = set()
opposite_territory = set()

team_names = set()

class Agent:
    def __init__(self, name):
        self.name = name
        self._idx = int(name.split('_')[1])
    
    def strategy(self, state):
        # Get the current position of the agent
        curr_pos = state['curr_pos']
        # Get the sensor data
        sensor_data = state['sensor']
        # Get capturable nodes
        capture_sensor_data = sensor_data[f'capture_{self.name}'][1]
        # Get the territory sensor data
        territory_sensor_data = sensor_data[f'territory_{self.name}'][1]

        for node_id in capture_sensor_data:
            capturable_nodes.add(node_id)
        for node_id in territory_sensor_data['red']: # change according to the team
            self_territory.add(node_id)
        for node_id in territory_sensor_data['blue']: # change according to the team
            opposite_territory.add(node_id)

        # Get the map sensor data
        map_sensor_data = sensor_data[f'map_{self._idx}'][1]
        # Get the agent sensor data
        agent_sensor_data = sensor_data[f'agent_{self._idx}'][1]

        # Update the nodes
        nodes.update(map_sensor_data['nodes'])
        # Convert curr_pos to node
        curr_pos = nodes[curr_pos]
        # Update the current opposite agents
        current_opposite_agents.update(
            {name: pos for name, pos in agent_sensor_data.items() if name not in team_names}
        )
        
        force = [0.0, 0.0] # initialize the force to 0
        # Calculate the force from capturable nodes
        for node_id in capturable_nodes:
            if node_id in nodes:
                node = nodes[node_id]
                dist = (node.x - curr_pos.x)**2 + (node.y - curr_pos.y)**2
                dist = dist/(random.random() + 1e-6)
                if dist < 1e-6:
                    continue
                force[0] += (node.x - curr_pos.x) / dist
                force[1] += (node.y - curr_pos.y) / dist
        
        # Calculate the force from opposite team agents
        for name, pos in current_opposite_agents.items():
            if pos in opposite_territory:
                if pos not in nodes:
                    continue
                node = nodes[pos]
                dist = (node.x - curr_pos.x)**2 + (node.y - curr_pos.y)**2
                if dist < 1e-6:
                    continue
                force[0] -= (node.x - curr_pos.x) / dist * (random.random() + 1e-6)
                force[1] -= (node.y - curr_pos.y) / dist * (random.random() + 1e-6)
            if pos in self_territory:
                if pos not in nodes:
                    continue
                node = nodes[pos]
                dist = (node.x - curr_pos.x)**2 + (node.y - curr_pos.y)**2
                if dist < 1e-6:
                    continue
                force[0] += (node.x - curr_pos.x) / dist * (random.random() + 1e-6)
                force[1] += (node.y - curr_pos.y) / dist * (random.random() + 1e-6)
        
        neighbors = sensor_data[f'neigh_{self._idx}'][1]

        neighbor_nodes = [nodes[neighbor] for neighbor in neighbors if neighbor in nodes]

        dot_products = {}

        # Calculate the force dot product
        for node in neighbor_nodes:
            dot_product = (node.x - curr_pos.x) * force[0] + (node.y - curr_pos.y) * force[1]
            dot_products[node.id] = dot_product + (0.5 - random.random()) * 0.1
        
        # Return the node with the maximum dot product
        max_node = max(dot_products, key=dot_products.get)
        state['action'] = max_node
    

# Mapper called by game to register the agents
def mapper(agent_names):
    ret = {}
    for name in agent_names:
        team_names.add(name)
        agent = Agent(name)
        ret[name] = agent.strategy
    
    return ret