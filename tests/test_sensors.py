#!/usr/bin/env python3
import gamms
import pickle
from gamms.typing.sensor_engine import SensorType
from gamms.SensorEngine.sensor_engine import SensorEngine

# --- Setup context, graph, sensors, and agents (as in your game example) ---
ctx = gamms.create_context()

# Load the graph from file and attach it to the context.
with open("graph.pkl", 'rb') as f:
    G = pickle.load(f)
ctx.graph.attach_networkx_graph(G)

# Create 10 dummy agents for testing.
for i in range(10):
    name = f"agent_{i}"
    agent_config = {
        'meta': {'team': 0},
        'sensors': [],
        'start_node_id': i
    }
    ctx.agent.create_agent(name, **agent_config)

# Create a SensorEngine instance.
sensor_engine = SensorEngine(ctx)

# --- Test MAP Sensor ---
# MAP sensor: using ArcSensor with range=inf and fov=360 should detect all nodes.
map_sensor = sensor_engine.create_sensor("map_test", SensorType.MAP)
map_sensor.sense(0)  # sense from node 0
print("=== MAP Sensor Output ===")
print("Nodes detected:", list(map_sensor.data.get('nodes', {}).keys()))
print("Agents detected:", list(map_sensor.data.get('agents', {}).keys()))

# --- Test RANGE Sensor ---
# RANGE sensor: using ArcSensor with finite range (30) and fov=360.
range_sensor = sensor_engine.create_sensor("range_test", SensorType.RANGE)
range_sensor.sense(0)  # sense from node 0
print("=== RANGE Sensor Output ===")
print("Nodes detected:", list(range_sensor.data.get('nodes', {}).keys()))
print("Agents detected:", list(range_sensor.data.get('agents', {}).keys()))

# --- Test ARC Sensor ---
# ARC sensor: using ArcSensor with finite range (30), a narrow fov (90), and orientation 0°.
arc_sensor = sensor_engine.create_sensor("arc_test", SensorType.ARC)
arc_sensor.sense(0)  # sense from node 0
print("=== ARC Sensor Output ===")
print("Nodes detected:", list(arc_sensor.data.get('nodes', {}).keys()))
print("Agents detected:", list(arc_sensor.data.get('agents', {}).keys()))

# --- Test AGENT Sensor ---
# Agent sensor: detects agents within a 30-unit range.
# We assign an owner so that the sensor does not detect its own agent.
agent_sensor = sensor_engine.create_sensor("agent_test", SensorType.AGENT)
agent_sensor.owner = "agent_0"  # skip detecting agent_0 (the owner)
agent_sensor.sense(0)  # sense from node 0
print("=== AGENT Sensor Output ===")
print("Agents detected:", list(agent_sensor.data.keys()))

ctx.terminate()
