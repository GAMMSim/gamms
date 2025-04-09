import gamms


VIS_ENGINE = gamms.visual.Engine.PYGAME # visual engine to use
GRID_SIZE = 20 # size of the grid

MAX_SIM_STEPS = 1000 # NUMBER OF STEPS IN THE SIMULATION

RED_TEAM_AGENTS = 10 # NUMBER OF AGENTS IN THE RED TEAM
BLUE_TEAM_AGENTS = 10 # NUMBER OF AGENTS IN THE BLUE TEAM

graph_vis_config = {
    'width': 1980, # width of the graph visualization
    'height': 1080, # height of the graph visualization
}

sensor_config = {}

for i in range(RED_TEAM_AGENTS + BLUE_TEAM_AGENTS):
    sensor_config[f'neigh_{i}'] = {
        'type': gamms.sensor.SensorType.NEIGHBOR, # type of the sensor
    }

agent_config = {}

for i in range(RED_TEAM_AGENTS):
    agent_config[f'agent_{i}'] = {
        'meta': {'team': 0}, # team of the agent
        'sensors': [f'neigh_{i}'], # sensors of the agent
        'start_node_id': i, # starting node id of the agent
    }

for i in range(RED_TEAM_AGENTS, RED_TEAM_AGENTS + BLUE_TEAM_AGENTS):
    agent_config[f'agent_{i}'] = {
        'meta': {'team': 1}, # team of the agent
        'sensors': [f'neigh_{i}'], # sensors of the agent
        'start_node_id': 400-1-i, # starting node id of the agent
    }

agent_vis_config = {}

for i in range(RED_TEAM_AGENTS):
    agent_vis_config[f'agent_{i}'] = {
        'color': (255, 0, 0), # color of the agent
        'size': 10, # size of the agent
    }

for i in range(RED_TEAM_AGENTS, RED_TEAM_AGENTS + BLUE_TEAM_AGENTS):
    agent_vis_config[f'agent_{i}'] = {
        'color': (0, 0, 255), # color of the agent
        'size': 10, # size of the agent
    }
