from gamms.typing import IContext
from gamms.typing.agent_engine import IAgent, IAgentEngine
from gamms.typing.opcodes import OpCodes
from typing import Callable, Dict, Any, Optional, Tuple
import math

class NoOpAgent(IAgent):
    def __init__(self, ctx: IContext, name, start_node_id, **kwargs):
        """Initialize the agent at a specific node with access to the graph and set the color."""
        self._ctx = ctx
        self._name = name
        self._prev_node_id = start_node_id
        self._current_node_id = start_node_id
    
    @property
    def name(self):
        return self._name
    
    @property
    def current_node_id(self):
        return self._current_node_id
    
    @current_node_id.setter
    def current_node_id(self, node_id):
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
    def prev_node_id(self):
        return self._prev_node_id
    
    @prev_node_id.setter
    def prev_node_id(self, node_id):
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
    def state(self):
        return {}
        
    @property
    def strategy(self):
        return 

    @strategy.setter
    def strategy(self, strategy):
        return
    
    def register_sensor(self, name, sensor):
        return
    
    def register_strategy(self, strategy):
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
    def __init__(self, ctx: IContext, name, start_node_id, **kwargs):
        """Initialize the agent at a specific node with access to the graph and set the color."""
        self._ctx = ctx
        self._graph = self._ctx.graph
        self._name = name
        self._sensor_list = {}
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
    def current_node_id(self):
        return self._current_node_id
    
    @current_node_id.setter
    def current_node_id(self, node_id):
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
    def prev_node_id(self):
        return self._prev_node_id
    
    @prev_node_id.setter
    def prev_node_id(self, node_id):
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

    @strategy.setter
    def strategy(self, strategy):
        self._strategy = strategy
    
    def register_sensor(self, name, sensor):
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
    
    def deregister_sensor(self, name):
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
    
    def register_strategy(self, strategy):
        self.strategy = strategy
    
    def step(self):
        if self._strategy is None:
            raise AttributeError("Strategy is not set.")
        state = self.get_state()
        self._strategy(state)
        self.set_state()

    def get_state(self) -> dict:
        for sensor in self._sensor_list.values():
            sensor.sense(self._current_node_id)

        state = {'curr_pos': self._current_node_id}
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

class AerialAgent(Agent):
    def __init__(self, ctx: IContext, name, start_node_id, speed, **kwargs):
        super().__init__(ctx, name, start_node_id, **kwargs)
        self._altitude = 0.0
        self._speed = speed  # Speed of the agent in units per second
        self._position = (0.0, 0.0, 0.0)  # position vector (x, y, z)
        self._orientation = (0.0, 0.0, 0.0, 0.0)  # orientation vector
        self._on_ground = True # Indicates if the agent is on the ground
        self.get_starting_position()
    
    def get_starting_position(self):
        """Set the starting position of the agent based on the start node."""
        start_node = self._graph.graph.get_node(self._current_node_id)
        self._position = (start_node.x, start_node.y, self._altitude)
        self._orientation = (0.0, 0.0, 0.0, 1.0)
    
    def get_state(self) -> dict:
        for sensor in self._sensor_list.values():
            sensor.sense(self._current_node_id)

        state = {}
        state['sensor'] = {k:(sensor.type, sensor.data) for k, sensor in self._sensor_list.items()}
        state['altitude'] = self._altitude
        state['speed'] = self._speed
        state['position'] = self._position
        state['orientation'] = self._orientation
        state['on_ground'] = self._on_ground
        self._state = state
    
    def set_state(self):
        self._position = self._state['action']
        self._altitude = self._position[2]
        self._on_ground = (self._altitude == 0)

class AgentEngine(IAgentEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        self.agents: Dict[str, IAgent] = {}

    def create_iter(self):
        return self.agents.values()
    
    def create_agent(self, name, **kwargs):
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.AGENT_CREATE, data={"name": name, "kwargs": kwargs})
        start_node_id = kwargs.pop('start_node_id')
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

    def delete_agent(self, name) -> None:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.AGENT_DELETE, data=name)
            
        if name not in self.agents:
            self.ctx.logger.warning(f"Deleting non-existent agent {name}")
        self.agents.pop(name, None)

    def terminate(self):
        return
    