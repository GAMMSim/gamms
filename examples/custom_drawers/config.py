# The file describes the configuration for the game
import gamms


# Visualization
vis_engine = gamms.visual.Engine.PYGAME

# The path to the graph file
location = "West Point, New York, USA"
resolution = 100.0
graph_path = 'graph.pkl'

# Sensor configuration
sensor_config = {
    'neigh_0': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_1': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_2': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_3': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_4': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_5': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_6': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_7': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_8': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_9': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'map': {
        'type': gamms.sensor.SensorType.MAP,
    },
    'agent': {
        'type': gamms.sensor.SensorType.AGENT,
    }
}

# The configuration of the agents
agent_config = {
    'agent_0': {
        'meta': {'team': 0},
        'sensors': ['neigh_0', 'map', 'agent'],
        'start_node_id': 0
    },
    'agent_1': {
        'meta': {'team': 0},
        'sensors': ['neigh_1', 'map', 'agent'],
        'start_node_id': 1
    },
    'agent_2': {
        'meta': {'team': 0},
        'sensors': ['neigh_2', 'map', 'agent'],
        'start_node_id': 2
    },
    'agent_3': {
        'meta': {'team': 0},
        'sensors': ['neigh_3', 'map', 'agent'],
        'start_node_id': 3
    },
    'agent_4': {
        'meta': {'team': 0},
        'sensors': ['neigh_4', 'map', 'agent'],
        'start_node_id': 4
    },
    'agent_5': {
        'meta': {'team': 1},
        'sensors': ['neigh_5', 'map', 'agent'],
        'start_node_id': 500
    },
    'agent_6': {
        'meta': {'team': 1},
        'sensors': ['neigh_6', 'map', 'agent'],
        'start_node_id': 501
    },
    'agent_7': {
        'meta': {'team': 1},
        'sensors': ['neigh_7', 'map', 'agent'],
        'start_node_id': 502
    },
    
    'agent_8': {
        'meta': {'team': 1},
        'sensors': ['neigh_8', 'map', 'agent'],
        'start_node_id': 503
    },
    'agent_9': {
        'meta': {'team': 1},
        'sensors': ['neigh_9', 'map', 'agent'],
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