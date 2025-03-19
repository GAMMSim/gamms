# The file describes the configuration for the game
import gamms
import math

# Visualization
vis_engine = gamms.visual.Engine.PYGAME

# The path to the graph file
location = "West Point, New York, USA"
resolution = 10.0
graph_path = 'graph.pkl'

# Sensor configuration
import math

sensor_config = {}

for i in range(0, 10):
    sensor_config[f'neigh_{i}'] = {
        'type': gamms.sensor.SensorType.NEIGHBOR
    }

for i in range(0, 10):
    sensor_config[f'range_{i}'] = {
        'type': gamms.sensor.SensorType.ARC,  
        'sensor_range': 30,  
        'fov': math.radians(90),
    }

for i in range(0, 10):
    sensor_config[f'agent_sense_{i}'] = {
        'type': gamms.sensor.SensorType.AGENT_ARC,  
        'sensor_range': 30,  
        'fov': math.radians(90),
    }

# The configuration of the agents
agent_config = {
    'agent_0': {
        'meta': {'team': 0},
        'sensors': ['neigh_0', 'range_0', 'agent_sense_0'],  
        'start_node_id': 0
    },
    'agent_1': {
        'meta': {'team': 0},
        'sensors': ['neigh_1', 'range_1', 'agent_sense_1'],  
        'start_node_id': 10
    },
    'agent_2': {
        'meta': {'team': 0},
        'sensors': ['neigh_2', 'range_2', 'agent_sense_2'],  
        'start_node_id': 20
    },
    'agent_3': {
        'meta': {'team': 0},
        'sensors': ['neigh_3', 'range_3', 'agent_sense_3'],  
        'start_node_id': 30
    },
    'agent_4': {
        'meta': {'team': 0},
        'sensors': ['neigh_4', 'range_4', 'agent_sense_4'],  
        'start_node_id': 40
    },
    'agent_5': {
        'meta': {'team': 1},
        'sensors': ['neigh_5', 'range_5', 'agent_sense_5'],  
        'start_node_id': 500
    },
    'agent_6': {
        'meta': {'team': 1},
        'sensors': ['neigh_6', 'range_6', 'agent_sense_6'], 
        'start_node_id': 501
    },
    'agent_7': {
        'meta': {'team': 1},
        'sensors': ['neigh_7', 'range_7', 'agent_sense_7'],  
        'start_node_id': 502
    },
    'agent_8': {
        'meta': {'team': 1},
        'sensors': ['neigh_8', 'range_8', 'agent_sense_8'],  
        'start_node_id': 503
    },
    'agent_9': {
        'meta': {'team': 1},
        'sensors': ['neigh_9', 'range_9', 'agent_sense_9'],  
        'start_node_id': 504
    }
}

# # Visualization configuration
graph_vis_config = {
    'width' : 1980,
    'height' : 1080
}

# # Visualization configuration for the agents
agent_vis_config = {
    'agent_0': {
        'color': 'blue',
        'size': 8,
    },
    'agent_1': {
        'color': 'blue',
        'size': 8,
    },
    'agent_2': {
        'color': 'blue',
        'size': 8,
    },
    'agent_3': {
        'color': 'blue',
        'size': 8,
    },
    'agent_4': {
        'color': 'blue',
        'size': 8,
    },
    'agent_5': {
        'color': 'red',
        'size': 8,
    },
    'agent_6': {
        'color': 'red',
        'size': 8,
    },
    'agent_7': {
        'color': 'red',
        'size': 8,
    },
    'agent_8': {
        'color': 'red',
        'size': 8,
    },
    'agent_9': {
        'color': 'red',
        'size': 8,
    }
}

sensor_vis_config = {}
for i in range(10):
    sensor_vis_config[f'neigh_{i}'] = {
        'color': 'purple',
        'size': 2,
        'layer': 25,
    }
    sensor_vis_config[f'range_{i}'] = {
        'node_color': 'cyan',
        'edge_color': 'cyan',
        'layer': 24,
    }
    sensor_vis_config[f'agent_sense_{i}'] = {
        'color': 'grey',
        'size': 8,
    }