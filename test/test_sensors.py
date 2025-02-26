#!/usr/bin/env python3
import gamms

import pickle
from gamms.typing.sensor_engine import SensorType
from gamms.SensorEngine.sensor_engine import RangeSensor, ArcSensor



# --- Setup context, graph, sensors, and agents (as in your game example) ---
ctx = gamms.create_context()


# Load the graph from file and attach it to the context.
with open("graph.pkl", 'rb') as f:
    G = pickle.load(f)
ctx.graph.attach_networkx_graph(G)


# Create agents using the agent_config.
for i in range(10):
    name = f"agent_{i}"
    agent = {
        'meta': {'team': 0},
        'sensors': [],
        'start_node_id': i
    }
    ctx.agent.create_agent(name, **agent)

# --- Test the RangeSensor ---
# Create a RangeSensor instance manually.
range_sensor = RangeSensor(
    ctx, 
    sensor_id="range_test", 
    sensor_type=SensorType.RANGE, 
    nodes=ctx.graph.graph.nodes, 
    sensor_range=30
)
# Run the sensor from a chosen node (e.g., node 0)
range_sensor.sense(0)
print("=== RangeSensor Output ===")
print("Nodes detected:", range_sensor.data.get('nodes').keys())
print("Agents detected:", range_sensor.data.get('agents').keys())

# --- Test the ArcSensor ---
# Create an ArcSensor instance manually.
# For example: 90° field-of-view, oriented upward (90°), with range 30.
arc_sensor = ArcSensor(
    ctx, 
    sensor_id="arc_test", 
    sensor_type=SensorType.RANGE, 
    nodes=ctx.graph.graph.nodes, 
    sensor_range=30, 
    fov=30, 
    orientation=90
)
# Run the sensor from the same node (node 0)
arc_sensor.sense(0)
print("=== ArcSensor Output ===")
print("Nodes detected:", arc_sensor.data.get('nodes').keys())
print("Agents detected:", arc_sensor.data.get('agents').keys())

ctx.terminate()
