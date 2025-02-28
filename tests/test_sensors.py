#!/usr/bin/env python3
import gamms
import pickle
import math
from gamms.typing.sensor_engine import SensorType
from gamms.SensorEngine.sensor_engine import SensorEngine

# --- Setup context, graph, sensors, and agents ---
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
        'start_node_id': i  # Each agent starts at a different node.
    }
    ctx.agent.create_agent(name, **agent_config)

# Simulate movement for agent_0 to update its orientation.
# Initially, agent_0 starts at node 0; now we update it to node 1.
agent0 = ctx.agent.get_agent("agent_0")
agent0.current_node_id = 1  # This will update agent0.orientation

# --- Create SensorEngine instance ---
sensor_engine = SensorEngine(ctx)

# --- Test MAP Sensor ---
# MAP sensor: using MapSensor (via ArcSensor) with range=inf and fov=360 should detect all nodes.
map_sensor = sensor_engine.create_sensor("map_test", SensorType.MAP)
map_sensor.sense(0)  # Sense from node 0
print("=== MAP Sensor Output ===")
print("Nodes detected:", list(map_sensor.data.get('nodes', {}).keys()))
# (MAP sensor doesn't process agents)

# --- Test RANGE Sensor ---
# RANGE sensor: using MapSensor with finite range (30) and fov=360.
range_sensor = sensor_engine.create_sensor("range_test", SensorType.RANGE)
range_sensor.sense(0)  # Sense from node 0
print("=== RANGE Sensor Output ===")
print("Nodes detected:", list(range_sensor.data.get('nodes', {}).keys()))

# --- Test ARC Sensor ---
# ARC sensor: using MapSensor with finite range (30) and a narrow fov (90).
# Set the owner so that the sensor automatically uses agent_0's orientation.
arc_sensor = sensor_engine.create_sensor("arc_test", SensorType.ARC)
arc_sensor.owner = "agent_0"
arc_sensor.sense(0)  # Sense from node 0; will use agent_0.orientation
print("=== ARC Sensor Output ===")
print("Nodes detected:", list(arc_sensor.data.get('nodes', {}).keys()))

# --- Test AGENT Sensor (full FOV) ---
# Agent sensor: detects agents within a 30-unit range (fov=360).
agent_sensor = sensor_engine.create_sensor("agent_test", SensorType.AGENT)
agent_sensor.owner = "agent_0"  # Skip detecting agent_0 (the owner)
agent_sensor.sense(0)  # Sense from node 0
print("=== AGENT Sensor Output (Full FOV) ===")
print("Agents detected:", list(agent_sensor.data.keys()))

# --- Test AGENT_ARC Sensor (directional agent sensor) ---
# Agent sensor with directional filtering: using fov=90.
agent_arc_sensor = sensor_engine.create_sensor("agent_arc_test", SensorType.AGENT_ARC)
agent_arc_sensor.owner = "agent_0"
agent_arc_sensor.sense(0)
print("=== AGENT_ARC Sensor Output (Directional) ===")
print("Agents detected:", list(agent_arc_sensor.data.keys()))

# --- Test AGENT_RANGE Sensor (full FOV agent sensor) ---
# Agent sensor configured as full-range (fov=360).
agent_range_sensor = sensor_engine.create_sensor("agent_range_test", SensorType.AGENT_RANGE)
agent_range_sensor.owner = "agent_0"
agent_range_sensor.sense(0)
print("=== AGENT_RANGE Sensor Output ===")
print("Agents detected:", list(agent_range_sensor.data.keys()))

ctx.terminate()
