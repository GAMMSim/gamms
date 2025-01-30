# The file describes the configuration for the game
import gamms


# Visualization
vis_engine = gamms.visual.Engine.PYGAME


# Graph Configuration
location = "West Point, New York, USA"
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