
# Sensors Overview and Examples

## Overview
Sensors allow agents to perceive and interact with other objects, agents, and their environment. They are integral components that enable agents to gather essential information about their surroundings for decision-making and actions.

## Types of Sensors

### Neighbor Sensor
- **Description**: Detects immediate neighbors directly connected to the agent's current position.
- **Functionality**:
  - Gathers nodes that share a direct edge with the current node.
  - Useful for local, direct adjacency awareness.

### Map Sensor
- **Description**: Detects environmental nodes within a specified range and/or field of view (FOV).
- **Modes**:
  - **Range Mode**: Defined by the maximum sensing distance.
  - **Field of View (FOV) Mode**: Defined by the angular width (in radians) around the agent's orientation.
- **Functionality**:
  - Supports multiple configurations:
    - **Map Sensor**: Infinite range, 360° sensing (`sensor_range = inf`, `fov = 2*pi`).
    - **Range Sensor**: Limited range, 360° sensing (`fov = 2*pi`).
    - **Directional Sensor**: Limited range and limited angular sensing (`fov < 2*pi`).
  - Stores detected nodes and connecting edges.

### Agent Sensor
- **Description**: Specialized sensor for detecting other agents within a defined range and/or field of view.
- **Modes**:
  - **Range Mode**: Limits the sensing distance.
  - **FOV Mode**: Limits the sensing angle around agent orientation.
- **Functionality**:
  - Can detect other agents, excluding the owner agent itself.
  - Orientation-aware sensing, allowing directional sensing.

## Creating a Custom Sensor
You can implement custom sensors for specialized use-cases. Use the provided `@custom()` decorator from the sensor engine to easily register new sensors.

### Example:
```python
@sensor_engine.custom()
class MyCustomSensor(ISensor):
    def __init__(self, custom_param):
        super().__init__()
        self.custom_param = custom_param

    def sense(self, node_id):
        # Implement custom sensing logic
        pass

    def update(self, data):
        # Implement update logic if required
        pass
```

## Example of Different Sensors

Here's a Python example illustrating how to create and use each type of built-in sensor using the provided `SensorEngine`:

```python
# Assume context 'ctx' is available and properly initialized.

# Create SensorEngine
sensor_engine = SensorEngine(ctx)

# Neighbor Sensor
neighbor_sensor = sensor_engine.create_sensor(
    sensor_id="neighbor_sensor_1",
    sensor_type=SensorType.NEIGHBOR
)
neighbor_sensor.set_owner("agent_1")
neighbor_sensor.sense(node_id=10)
print("Neighbors:", neighbor_sensor.data)

# Map Sensor with Infinite Range (Full map sensing)
map_sensor = sensor_engine.create_sensor(
    sensor_id="map_sensor_full",
    sensor_type=SensorType.MAP
)
map_sensor.set_owner("agent_1")
map_sensor.sense(node_id=10)
print("All visible nodes and edges:", map_sensor.data)

# Range Sensor (Limited Range, 360-degree FOV)
range_sensor = sensor_engine.create_sensor(
    sensor_id="range_sensor_1",
    sensor_type=SensorType.RANGE,
    sensor_range=50
)
range_sensor.set_owner("agent_1")
range_sensor.sense(node_id=10)
print("Nodes within range:", range_sensor.data)

# Arc Sensor (Limited Range and Limited FOV)
arc_sensor = sensor_engine.create_sensor(
    sensor_id="arc_sensor_1",
    sensor_type=SensorType.ARC,
    sensor_range=50,
    fov=math.pi / 2  # 90-degree FOV
)
arc_sensor.set_owner("agent_1")
arc_sensor.sense(node_id=10)
print("Nodes within arc:", arc_sensor.data)

# Agent Sensor (Detect other agents within range)
agent_sensor = sensor_engine.create_sensor(
    sensor_id="agent_sensor_1",
    sensor_type=SensorType.AGENT,
    sensor_range=30
)
agent_sensor.set_owner("agent_1")
agent_sensor.sense(node_id=10)
print("Agents detected within range:", agent_sensor.data)

# Agent Arc Sensor (Directional Agent Detection)
agent_arc_sensor = sensor_engine.create_sensor(
    sensor_id="agent_arc_sensor_1",
    sensor_type=SensorType.AGENT_ARC,
    sensor_range=30,
    fov=math.radians(90)
)
agent_arc_sensor.set_owner("agent_1")
agent_arc_sensor.sense(node_id=10)
print("Agents detected within arc:", agent_arc_sensor.data)
```
