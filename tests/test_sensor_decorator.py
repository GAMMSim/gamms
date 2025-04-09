import gamms
from gamms.typing.sensor_engine import SensorType, ISensor

# --- Setup a minimal real context similar to game.py ---


# Create a gamms context.
ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)



# Obtain the sensor engine from the context.
sensor_engine = ctx.sensor

# Define a custom sensor using the sensor_engine.custom decorator.
@sensor_engine.custom(name='TEST')
class CustomSensor(ISensor):
    def __init__(self, extra_param=None):
        # extra_param is just to demonstrate passing additional arguments.
        self.extra_param = extra_param

    def sense(self, node_id: int) -> None:
        # Minimal implementation for testing.
        print(f"Sensing node: {node_id}")
    
    def set_owner(self, owner: str) -> None:
        # Set the owner of the sensor.
        self.owner = owner
    
    @property
    def type(self) -> SensorType:
        # Return the type of the sensor.
        return SensorType.CUSTOM

    @property
    def data(self):
        return 

    def update(self, data: dict) -> None:
        print(f"Updating sensor with data: {data}")

# --- Instantiate and test custom sensors ---

# Create the first custom sensor instance with name "CustomA"
sensor1 = CustomSensor(extra_param=42)
# Create the second custom sensor instance with name "CustomB"
sensor2 = CustomSensor(extra_param=100)

# Print the custom_data dictionary to verify initialization.
print("Sensor1 type:", sensor1.type)
print("Sensor2 type:", sensor2.type)

# Optionally, exercise the sensor methods.
sensor1.sense(0)
sensor2.update({"sample": 123})

# Terminate the context.
ctx.terminate()
