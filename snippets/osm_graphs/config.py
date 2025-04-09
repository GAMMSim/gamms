import gamms


VIS_ENGINE = gamms.visual.Engine.PYGAME # visual engine to use

XML_FILE = 'La_Jolla.osm' # OSM XML file
RESOLUTION = 100.0 # resolution of the graph in meters
TOLERANCE = 0.01 # tolerance for the graph in meters
BIDIRECTIONAL = False # whether the graph is bidirectional or not

MAX_SIM_STEPS = 10000 # NUMBER OF STEPS IN THE SIMULATION
TERRITORY_RADIUS = 500.0 # radius of the territory in meters
STEP_INCREMENT = 100 # increment for the simulation steps
MIN_SIM_STEPS = 5000 # minimum number of steps in the simulation

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
    }

for i in range(RED_TEAM_AGENTS, RED_TEAM_AGENTS + BLUE_TEAM_AGENTS):
    agent_config[f'agent_{i}'] = {
        'meta': {'team': 1}, # team of the agent
        'sensors': [f'neigh_{i}'], # sensors of the agent
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
