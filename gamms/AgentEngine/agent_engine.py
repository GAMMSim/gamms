from gamms.typing import IContext
from gamms.typing.agent_engine import IAgent, IAgentEngine

from typing import Callable, Dict, Any, Optional, List


#I think state might also have to be a property

class Agent(IAgent):
    def __init__(self, ctx, name, start_node_id, **kwargs):
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
    
    def current_node_id(self):
        return self._current_node_id
    
    @current_node_id.setter
    def current_node_id(self, node_id):
        if self._ctx.record.record():
            self._ctx.write(opCode=5, data=node_id)
        self._current_node_id = node_id
    
    def prev_node_id(self):
        return self._prev_node_id
    
    @prev_node_id.setter
    def prev_node_id(self, node_id):
        if self._ctx.record.record():
            self._ctx.write(opCode=6, data=node_id)
        self._prev_node_id = node_id
    
    def state(self):
        return self._state
    
    @state.setter
    def state(self, state):
        if self._ctx.record.record():
            self._ctx.write(opCode=7, data=state)
        self._state = state
    
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy):
        if self._ctx.record.record():
            self._ctx.write(opCode=8, data=strategy)
        self._strategy = strategy
    
    def register_sensor(self, name, sensor):
        self._sensor_list[name] = sensor
    
    def register_strategy(self, strategy):
        self.strategy = strategy
    
    def step(self, state: dict):
        if self._strategy is None:
            raise AttributeError("Strategy is not set.")
        state = self.get_agent_state()
        self._strategy(state)
        self.set_agent_state()
        if self._ctx.record.record():
            self._ctx.write(opCode=2, data=state)

    def get_agent_state(self) -> dict:
        if self._ctx.record.record():
            self._ctx.write(opCode=3, data=state)
        for sensor in self._sensor_list.values():
            sensor.sense(self._current_node_id)

        state = {'curr_pos': self._current_node_id}
        state['sensor'] = {k:(sensor.type, sensor.data) for k, sensor in self._sensor_list.items()}
        self.state = state
        return self._state
    
    # def set_state(self) -> None:
    #     self._prev_node_id = self._current_node_id
    #     self._current_node_id = self._state['action']

    def set_agent_state(self) -> None:
        if self._ctx.record.record():
            self._ctx.write(opCode=4, data=self._state)
        self.prev_node_id = self._current_node_id
        self.current_node_id = self._state['action']
    


class AgentEngine(IAgentEngine):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        self.agents: Dict[str, IAgent] = {}

    def create_iter(self):
        return self.agents.values()
    
    def create_agent(self, name, **kwargs):
        start_node_id = kwargs.pop('start_node_id')
        agent = Agent(self.ctx, name, start_node_id, **kwargs)
        for sensor in kwargs['sensors']:
            agent.register_sensor(sensor, self.ctx.sensor.get_sensor(sensor))
        if name in self.agents:
            raise ValueError(f"Agent {name} already exists.")
        self.agents[name] = agent
        return agent
    
    def get_agent(self, name: str) -> IAgent:
        if self.ctx.record.record():
            self.ctx.write(opCode=0, data=name)

        if name in self.agents:
            return self.agents[name]
        else:
            raise ValueError(f"Agent {name} not found.")

    def delete_agent(self, name) -> None:
        if self.ctx.record.record():
            self.ctx.write(opCode=1, data=name)
        if name not in self.agents:
            print("Warning: Deleting non-existent agent")
        self.agents.pop(name, None)

    def terminate(self):
        return
    