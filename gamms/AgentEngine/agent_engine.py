from gamms.typing import (
    IContext,
    ISensor,
    IAgent,
    OpCodes,
    IAgentEngine,
    IAerialAgent,
    AgentType,
)
from typing import Callable, Dict, Any, Optional, Tuple, cast
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
        self._orientation = (0.0, 0.0)
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    @property
    def type(self) -> AgentType:
        return AgentType.BASIC
    
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
        # Action can either be a node ID or a dictionary with 'action' key
        if isinstance(self._state['action'], int): # Node ids are integers
            # Check if the node exists in the graph
            _ = self._ctx.graph.graph.get_node(self._state['action'])
            self.current_node_id = self._state['action']
        elif isinstance(self._state['action'], dict):
            action = cast(Dict[str, Any], self._state['action'])
            if 'node_id' not in action:
                raise ValueError("Action dictionary must contain 'node_id' key.")
            else:
                _ = self._ctx.graph.graph.get_node(action['node_id'])
                self.current_node_id = action['node_id']
            
            if 'orientation' in action:
                orientation = cast(Tuple[float, float], action['orientation'])
                if len(orientation) != 2:
                    raise ValueError("Orientation must be a tuple of (sin, cos).")
                self.orientation = orientation
        else:
            raise TypeError("Action must be an integer (node ID) or a dictionary with 'node_id' key.")
            
    
    @property
    def orientation(self) -> Tuple[float, float]:
        """
        Calculate the orientation as sin and cos of the angle.
        The angle is calculated using the difference between the current and previous node positions.
        If the distance is zero, return (0.0, 0.0).
        """
        if self._orientation != (0.0, 0.0):
            return self._orientation
        prev_node = self._graph.graph.get_node(self.prev_node_id)
        curr_node = self._graph.graph.get_node(self.current_node_id)
        delta_x = curr_node.x - prev_node.x
        delta_y = curr_node.y - prev_node.y
        distance = math.sqrt(delta_x**2 + delta_y**2)
        if distance == 0:
            return (0.0, 0.0)
        else:
            return (delta_x / distance, delta_y / distance)
    
    @orientation.setter
    def orientation(self, orientation: Tuple[float, float]):
        """
        Set the orientation of the agent.
        The orientation is a tuple of (sin, cos).
        """
        if len(orientation) != 2:
            raise ValueError("Orientation must be a tuple of (sin, cos).")
        dist = math.sqrt(orientation[0]**2 + orientation[1]**2)
        if dist == 0:
            raise ValueError("Orientation cannot be a zero vector.")
        orientation = (orientation[0]/dist, orientation[1]/dist)
        self._orientation = orientation
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AGENT_ORIENTATION,
                data={
                    "agent_name": self.name,
                    "orientation": [orientation[0], orientation[1]],
                }
            )


class AerialAgent(IAerialAgent):
    def __init__(self, ctx: IContext, name: str, start_node_id: int, speed: float):
        self._ctx = ctx
        self._name = name
        self._sensor_list: Dict[str, ISensor] = {}
        self._strategy: Optional[Callable[[Dict[str, Any]], None]] = None
        self._state: Dict[str, Any] = {}
        self._quat = (1.0, 0.0, 0.0, 0.0)  # Default quaternion (no rotation)
        node = self._ctx.graph.graph.get_node(start_node_id)
        self._position = (node.x, node.y, 0.0)  # Default position at the node's coordinates with z=0.0
        self._prev_position = self._position
        self._prev_node_id = start_node_id
        self._speed = speed  # Speed of the aerial agent

    @property
    def type(self) -> AgentType:
        return AgentType.AERIAL
    
    @property
    def name(self):
        return self._name
        
    @property
    def position(self) -> Tuple[float, float, float]:
        return self._position

    @property
    def speed(self) -> float:
        return self._speed
    
    @position.setter
    def position(self, pos: Tuple[float, float, float]):
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AERIAL_AGENT_POSITION,
                data={
                    "agent_name": self.name,
                    "position": [pos[0], pos[1], pos[2]],
                }
            )
        self.prev_node_id = self.current_node_id  # Update previous node ID
        self._prev_position = self._position
        self._position = pos

    @property
    def prev_position(self):
        return self._prev_position
    
    @property
    def quat(self) -> Tuple[float, float, float, float]:
        """
        Get the quaternion representation of the agent's orientation.
        Formatted as (w, x, y, z).
        """
        norm = math.sqrt(self._quat[0]**2 + self._quat[1]**2 + self._quat[2]**2 + self._quat[3]**2)
        if norm == 0:
            return (1.0, 0.0, 0.0, 0.0)
        # Normalize the quaternion
        return (self._quat[0] / norm, self._quat[1] / norm, self._quat[2] / norm, self._quat[3] / norm)
    
    @quat.setter
    def quat(self, quat: Tuple[float, float, float, float]):
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AERIAL_AGENT_QUATERNION,
                data={
                    "agent_name": self.name,
                    "quat": [quat[0], quat[1], quat[2], quat[3]],
                }
            )
        self._quat = quat

    @property
    def orientation(self) -> Tuple[float, float]:
        """
        Calculate the orientation using the quaternion.
        """
        w, x, y, z = self.quat
        sin_theta = 2 * (w * y - x * z)
        cos_theta = 1 - 2 * (y**2 + z**2)
        return (cos_theta, sin_theta)

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
    def current_node_id(self) -> int:
        prev_node = self._ctx.graph.graph.get_node(self._prev_node_id)
        d = max(0.001, abs(self.position[0] - prev_node.x))
        d = max(d, abs(self.position[1] - prev_node.y))
        max_d = (d + 0.001)**2
        ret = -1
        for node_id in self._ctx.graph.graph.get_nodes(x=self.position[0], y=self.position[1], d=d):
            node = self._ctx.graph.graph.get_node(node_id)
            dist = (node.x - self.position[0])**2 + (node.y - self.position[1])**2
            if dist < max_d:
                ret = node_id
                max_d = dist
        if ret == -1:
            max_d = float("inf")
            ret = -1
            for node_id in self._ctx.graph.graph.get_nodes():
                node = self._ctx.graph.graph.get_node(node_id)
                dist = (node.x - self.position[0])**2 + (node.y - self.position[1])**2
                if dist < max_d:
                    ret = node_id
                    max_d = dist
        return ret
    
    @current_node_id.setter
    def current_node_id(self, node_id: int):
        node = self._ctx.graph.graph.get_node(node_id)
        if self._ctx.record.record():
            self._ctx.record.write(
                opCode=OpCodes.AGENT_CURRENT_NODE,
                data={
                    "agent_name": self.name,
                    "node_id": node_id,
                }
            )
        self.position = (node.x, node.y, self.position[2])
    
    @property
    def state(self) -> Dict[str, Any]:
        return self._state
    
    @property
    def strategy(self) -> Optional[Callable[[Dict[str, Any]], None]]:
        return self._strategy
    
    register_sensor = Agent.register_sensor
    deregister_sensor = Agent.deregister_sensor
    register_strategy = Agent.register_strategy
    step = Agent.step

    def get_state(self) -> Dict[str, Any]:
        for sensor in self._sensor_list.values():
            sensor.sense(self.current_node_id)

        state: Dict[str, Any] = {'curr_pos': self.position, 'quat': self.quat}
        state['sensor'] = {k:(sensor.type, sensor.data) for k, sensor in self._sensor_list.items()}
        self._state = state
        return self._state
    
    def set_state(self) -> None:
        if isinstance(self._state['action'], tuple):
            action = cast(Tuple[float, float, float], self._state['action'])
            if len(action) != 3:
                raise ValueError("Action must be a 3d tuple (x, y, z).")
            pos = self.position
            norm = math.sqrt(action[0]**2 + action[1]**2 + action[2]**2)
            if norm == 0:
                self.position = pos
            else:
                self.position = (
                    pos[0] + action[0] / norm * self._speed,
                    pos[1] + action[1] / norm * self._speed,
                    pos[2] + action[2] / norm * self._speed
                )
        elif isinstance(self._state['action'], dict):
            action = cast(Dict[str, Any], self._state['action'])
            if 'direction' in action:
                direction = cast(Tuple[float, float, float], action['direction'])
                if len(direction) != 3:
                    raise ValueError("Direction must be a 3d tuple (x, y, z).")
                pos = self.position
                norm = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
                if norm == 0:
                    self.position = pos
                else:
                    self.position = (
                        pos[0] + direction[0] / norm * self._speed,
                        pos[1] + direction[1] / norm * self._speed,
                        pos[2] + direction[2] / norm * self._speed
                    )
            if 'quat' in action:
                quat = action['quat']
                if len(quat) != 4:
                    raise ValueError("Quaternion must be a tuple of (w, x, y, z).")
                self.quat = (quat[0], quat[1], quat[2], quat[3])
        else:
            raise TypeError("Action must be a 3d tuple or a dictionary with 'direction' key.")

    
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
        agent_type = kwargs.pop('type', AgentType.BASIC)
        if agent_type == AgentType.AERIAL:
            speed = cast(float, kwargs.pop('speed'))
            agent = AerialAgent(self.ctx, name, start_node_id, speed)
        else:
            agent = Agent(self.ctx, name, start_node_id, **kwargs)

        if name in self.agents:
            raise ValueError(f"Agent {name} already exists.")
        self.agents[name] = agent

        for sensor in sensors:
            try:
                agent.register_sensor(sensor, self.ctx.sensor.get_sensor(sensor))
            except KeyError:
                self.ctx.logger.warning(f"Ignoring sensor {sensor} for agent {name}")
               
        return agent
    
    def get_agent(self, name: str) -> IAgent:
        if name in self.agents:
            return self.agents[name]
        else:
            raise KeyError(f"Agent {name} not found.")

    def delete_agent(self, name: str) -> None:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.AGENT_DELETE, data={'name' :name})
            
        if name not in self.agents:
            self.ctx.logger.warning(f"Deleting non-existent agent {name}")
        self.agents.pop(name, None)

    def terminate(self):
        return
    
