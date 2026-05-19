"""SensorEngine factory.

The actual sensor classes live in:
- ``sensors_basic`` — NeighborSensor, MapSensor, AgentSensor
- ``sensors_aerial`` — AerialSensor, AerialAgentSensor
- ``sensors_occluded`` — OccludedMapSensor, OccludedAgentSensor,
  OccludedAerialSensor, OccludedAerialAgentSensor (one general class per axis;
  ARC/RANGE variants are factory presets only).
"""

import math
from typing import Any, Callable, Dict, cast

from aenum import extend_enum

from gamms.typing import (
    IContext,
    ISensor,
    ISensorEngine,
    SensorType,
)
from gamms.SensorEngine.sensors_basic import AgentSensor, MapSensor, NeighborSensor
from gamms.SensorEngine.sensors_aerial import AerialAgentSensor, AerialSensor
from gamms.SensorEngine.sensors_occluded import (
    OccludedAerialAgentSensor,
    OccludedAerialSensor,
    OccludedAgentSensor,
    OccludedMapSensor,
)


class SensorEngine(ISensorEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        self.sensors: Dict[str, ISensor] = {}

    def create_sensor(self, sensor_id: str, sensor_type: SensorType, **kwargs: Dict[str, Any]) -> ISensor:
        if sensor_type == SensorType.NEIGHBOR:
            sensor: ISensor = NeighborSensor(self.ctx, sensor_id, sensor_type)
        elif sensor_type == SensorType.MAP:
            sensor = MapSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=float('inf'),
                fov=2 * math.pi,
            )
        elif sensor_type == SensorType.RANGE:
            sensor = MapSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=2 * math.pi,
            )
        elif sensor_type == SensorType.ARC:
            sensor = MapSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
            )
        elif sensor_type == SensorType.AGENT:
            sensor = AgentSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=float('inf'),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
            )
        elif sensor_type == SensorType.AGENT_ARC:
            sensor = AgentSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
            )
        elif sensor_type == SensorType.AGENT_RANGE:
            sensor = AgentSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', 30.0)),
                fov=2 * math.pi,
            )
        elif sensor_type == SensorType.AERIAL:
            sensor = AerialSensor(
                self.ctx, sensor_id,
                sensor_range=cast(float, kwargs.get('sensor_range', 100.0)),
                fov=cast(float, kwargs.get('fov', math.pi / 3)),
                quat=cast(tuple, kwargs.get('quat', (0.0, 0.0, 1.0, 0.0))),
            )
        elif sensor_type == SensorType.AERIAL_AGENT:
            sensor = AerialAgentSensor(
                self.ctx, sensor_id,
                sensor_range=cast(float, kwargs.get('sensor_range', 100.0)),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
                quat=cast(tuple, kwargs.get('quat', (1.0, 0.0, 0.0, 0.0))),
            )
        elif sensor_type == SensorType.OCCLUDED_MAP:
            sensor = OccludedMapSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', float('inf'))),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
                observer_height=cast(float, kwargs.get('observer_height', 1.6)),
            )
        elif sensor_type == SensorType.OCCLUDED_AGENT:
            sensor = OccludedAgentSensor(
                self.ctx, sensor_id, sensor_type,
                sensor_range=cast(float, kwargs.get('sensor_range', float('inf'))),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
                observer_height=cast(float, kwargs.get('observer_height', 1.6)),
            )
        elif sensor_type == SensorType.OCCLUDED_AERIAL:
            sensor = OccludedAerialSensor(
                self.ctx, sensor_id,
                sensor_range=cast(float, kwargs.get('sensor_range', 100.0)),
                fov=cast(float, kwargs.get('fov', math.pi / 3)),
                quat=cast(tuple, kwargs.get('quat', (math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0))),
            )
        elif sensor_type == SensorType.OCCLUDED_AERIAL_AGENT:
            sensor = OccludedAerialAgentSensor(
                self.ctx, sensor_id,
                sensor_range=cast(float, kwargs.get('sensor_range', 100.0)),
                fov=cast(float, kwargs.get('fov', 2 * math.pi)),
                quat=cast(tuple, kwargs.get('quat', (1.0, 0.0, 0.0, 0.0))),
            )
        else:
            raise ValueError("Invalid sensor type")
        self.add_sensor(sensor)
        return sensor

    def add_sensor(self, sensor: ISensor) -> None:
        sensor_id = sensor.sensor_id
        if sensor_id in self.sensors:
            raise ValueError(f"Sensor {sensor_id} already exists.")
        self.sensors[sensor_id] = sensor

    def get_sensor(self, sensor_id: str) -> ISensor:
        try:
            return self.sensors[sensor_id]
        except KeyError:
            raise KeyError(f"Sensor {sensor_id} not found.")

    def custom(self, name: str) -> Callable[[ISensor], ISensor]:
        if hasattr(SensorType, name):
            self.ctx.logger.warning(f"SensorType {name} already exists. Type has been set previously in current process.")
        else:
            extend_enum(SensorType, name, len(SensorType))
        val = getattr(SensorType, name)

        def decorator(cls_type: ISensor) -> ISensor:
            cls_type.type = property(lambda obj: val)
            return cls_type
        return decorator

    def terminate(self):
        return
