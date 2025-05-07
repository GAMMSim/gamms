from gamms.typing import (
    IContext,
    ISensor,
    IAgent,
    OpCodes,
    IAgentEngine,
    SensorType,
)
from typing import Callable, Dict, Any, Optional, Tuple, Union, List, cast
import math

class NoOpAgent(IAgent):
    def __init__(self, ctx: IContext, name: str, start_node_id: int, **kwargs: Dict[str, Any]):
        """Initialize the agent at a specific node with access to the graph and set the color."""
        self._ctx = ctx
        self._name = name
        self._prev_node_id = start_node_id
        self._current_node_id = start_node_id
    
    @property
    def name(self):
        return self._name
    
    @property
    def current_node_id(self) -> int:
        return self._current_node_id
    
    @current_node_id.setter
    def current_node_id(self, node_id: int):
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AGENT_CURRENT_NODE,
                data={
                    "agent_name": self.name,
                    "node_id": node_id,
                }
            )
        self._current_node_id = node_id

    @property
    def prev_node_id(self) -> int:
        return self._prev_node_id
    
    @prev_node_id.setter
    def prev_node_id(self, node_id: int):
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AGENT_PREV_NODE,
                data={
                    "agent_name": self.name,
                    "node_id": node_id
                }
            )
        self._prev_node_id = node_id

    
    @property
    def state(self) -> Dict[str, Any]:
        return {}
        
    @property
    def strategy(self):
        return 
    
    def register_sensor(self, name: str, sensor: ISensor):
        return
    
    def register_strategy(self, strategy: Callable[[Dict[str, Any]], None]):
        return
    
    def step(self):
        if self._strategy is None:
            raise AttributeError("Strategy is not set.")
        state = self.get_state()
        self._strategy(state)
        self.set_state()


    def get_state(self) -> dict:
        return {}
    
    def set_state(self) -> None:
        return

class Agent(IAgent):
    def __init__(self, ctx: IContext, name: str, start_node_id: int, **kwargs: Dict[str, Any]):
        """Initialize the agent at a specific node with access to the graph and set the color."""
        self._ctx = ctx
        self._graph = self._ctx.graph
        self._name = name
        self._sensor_list: Dict[str, ISensor] = {}
        self._prev_node_id = start_node_id
        self._current_node_id = start_node_id
        self._strategy: Optional[Callable[[Dict[str, Any]], None]] = None
        self._state = {}
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    @property
    def name(self):
        return self._name
    
    @property
    def current_node_id(self) -> int:
        return self._current_node_id
    
    @current_node_id.setter
    def current_node_id(self, node_id: int):
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AGENT_CURRENT_NODE,
                data={
                    "agent_name": self.name,
                    "node_id": node_id,
                }
            )
        self._current_node_id = node_id

    @property
    def prev_node_id(self) -> int:
        return self._prev_node_id
    
    @prev_node_id.setter
    def prev_node_id(self, node_id: int):
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AGENT_PREV_NODE,
                data={
                    "agent_name": self._name,
                    "node_id": node_id
                }
            )
        self._prev_node_id = node_id

    
    @property
    def state(self):
        return self._state
        
    @property
    def strategy(self):
        return self._strategy
    
    def register_sensor(self, name: str, sensor: ISensor):
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AGENT_SENSOR_REGISTER,
                data={
                    "agent_name": self.name,
                    "name": name,
                    "sensor_id": sensor.sensor_id,
                }
            )
        sensor.set_owner(self._name)
        self._sensor_list[name] = sensor
    
    def deregister_sensor(self, name: str):
        if name in self._sensor_list:
            sensor = self._sensor_list[name]
            if self._ctx.record.record():
                self._ctx.record.write(
                    opCode=OpCodes.AGENT_SENSOR_DEREGISTER,
                    data={
                        "agent_name": self.name,
                        "name": name,
                        "sensor_id": sensor.sensor_id,
                    }
                )
            sensor.set_owner(None)
            del self._sensor_list[name]
        else:
            self._ctx.logger.warning(f"Sensor {name} not found in agent {self._name}.")
    
    def register_strategy(self, strategy: Callable[[Dict[str, Any]], None]):
        self._strategy = strategy
    
    def step(self):
        if self._strategy is None:
            raise AttributeError("Strategy is not set.")
        state = self.get_state()
        self._strategy(state)
        self.set_state()

    def get_state(self) -> Dict[str, Any]:
        for sensor in self._sensor_list.values():
            sensor.sense(self._current_node_id)

        state: Dict[str, Any] = {'curr_pos': self._current_node_id}
        state['sensor'] = {k:(sensor.type, sensor.data) for k, sensor in self._sensor_list.items()}
        self._state = state
        return self._state
    

    def set_state(self) -> None:
        self.prev_node_id = self._current_node_id
        self.current_node_id = self._state['action']
    
    @property
    def orientation(self) -> Tuple[float, float]:
        """
        Calculate the orientation as sin and cos of the angle.
        The angle is calculated using the difference between the current and previous node positions.
        If the distance is zero, return (0.0, 0.0).
        """
        prev_node = self._graph.graph.get_node(self.prev_node_id)
        curr_node = self._graph.graph.get_node(self.current_node_id)
        delta_x = curr_node.x - prev_node.x
        delta_y = curr_node.y - prev_node.y
        distance = math.sqrt(delta_x**2 + delta_y**2)
        if distance == 0:
            return (0.0, 0.0)
        else:
            return (delta_x / distance, delta_y / distance)

class AgentEngine(IAgentEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        self.agents: Dict[str, IAgent] = {}

    def create_iter(self):
        return self.agents.values()
    
    def create_agent(self, name: str, **kwargs: Dict[str, Any]) -> IAgent:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.AGENT_CREATE, data={"name": name, "kwargs": kwargs})
        start_node_id = cast(int, kwargs.pop('start_node_id'))
        sensors = kwargs.pop('sensors', [])
        agent = Agent(self.ctx, name, start_node_id, **kwargs)
        for sensor in sensors:
            try:
                agent.register_sensor(sensor, self.ctx.sensor.get_sensor(sensor))
            except KeyError:
                self.ctx.logger.warning(f"Ignoring sensor {sensor} for agent {name}")
        if name in self.agents:
            raise ValueError(f"Agent {name} already exists.")
        self.agents[name] = agent
       
        return agent
    
    def get_agent(self, name: str) -> IAgent:
        if name in self.agents:
            return self.agents[name]
        else:
            raise KeyError(f"Agent {name} not found.")

    def delete_agent(self, name: str) -> None:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.AGENT_DELETE, data=name)
            
        if name not in self.agents:
            self.ctx.logger.warning(f"Deleting non-existent agent {name}")
        self.agents.pop(name, None)

    def terminate(self):
        return
    