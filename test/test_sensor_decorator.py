import gamms
from gamms.typing.sensor_engine import SensorType, ISensor

# --- Setup a minimal real context similar to game.py ---


# Create a gamms context.
ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)



# Obtain the sensor engine from the context.
sensor_engine = ctx.sensor

# Define a custom sensor using the sensor_engine.custom decorator.
@sensor_engine.custom(struct={'threshold': float, 'active': bool})
class CustomSensor(ISensor):
    def __init__(self, extra_param=None):
        # extra_param is just to demonstrate passing additional arguments.
        self.extra_param = extra_param

    def sense(self, node_id: int) -> None:
        # Minimal implementation for testing.
        print(f"[{self.custom_data['name']}] Sensing node: {node_id}")
    
    def data(self):
        return 

    def update(self, data: dict) -> None:
        print(f"[{self.custom_data['name']}] Updating sensor with data: {data}")

# --- Instantiate and test custom sensors ---

# Create the first custom sensor instance with name "CustomA"
sensor1 = CustomSensor("CustomA", extra_param=42)
# Create the second custom sensor instance with name "CustomB"
sensor2 = CustomSensor("CustomB", extra_param=100)

# Print the custom_data dictionary to verify initialization.
print("Sensor1 custom_data:", sensor1.custom_data)
print("Sensor2 custom_data:", sensor2.custom_data)

# Print the SensorType enum members dynamically added.
print("SensorType for CUSTOMA:", getattr(SensorType, "CUSTOMA"))
print("SensorType for CUSTOMB:", getattr(SensorType, "CUSTOMB"))

# Print the current custom sensor counter (should reflect two registrations).
print("Custom sensor counter:", sensor_engine.custom_sensor_counter)

# Print the engine's registry of custom sensor classes.
print("Registered custom sensors:", sensor_engine.custom_sensors)

# Optionally, exercise the sensor methods.
sensor1.sense(0)
sensor2.update({"sample": 123})

# Terminate the context.
ctx.terminate()
