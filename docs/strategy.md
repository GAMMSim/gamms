# Developing Agent Strategies

The simulator treats strategies as a function that maps the state of the agent to an action. The state contains information about the agent's location as well as the data collected from the sensors. The action is the movement of the agent in the environment.

## Understanding the Agent State

The agent state is a dictionary that has the following base structure:

```python
state = {
    'curr_pos': (integer) # The location id of the node where the agent is currently located
    'sensor' : {
        'sensor1': (Sensor 1 Type, Sensor 1 Data), # The data collected by sensor 1
        'sensor2': (Sensor 2 Type, Sensor 2 Data), # The data collected by sensor 2
        ...
    }
}
```
The exact structure depends on what type of sensors are associated with the agent. This will become clearer as we dive into the examples later.

The user needs to tell where the agent will move. To do that, the user only needs to add an additional key called `'action'` to the state dictionary. Note that it should be the inputed state dictionary that is modified and returned. In essence, the strategy function should look like this:

```python
def strategy(state):
    # Do something with the state
    state['action'] = (integer) # The location id of the node where the agent will move
    return
```

It is also possible that this strategy function is inside an agent class. This is useful when the agent has some internal state that needs to be maintained. There are no restrictions on how the class should be defined. The only requirement is that the class should have a method that takes state as input and updates the state with the action.

```python
class Agent:
    def __init__(self, arguements):
        # Initialize the agent
        pass

    def strategy(self, state):
        # Do something with the state
        state['action'] = (integer) # The location id of the node where the agent will move
        return
```

## Defining the Mapping Function

The game will try to import the `map_strategy` function from the strategy file. For the strategies to work, the user needs to define this function. The function is given an `agent_config` dictionary that contains the configuration of the agents in the game. The user needs to return a dictionary that maps the keys of the `agent_config` to the respective strategy functions. A typical `agent_config` dictionary looks like the following:

```python
agent_config = {
    'agent_0': {
        'meta': {'team': 0},
        'sensors': ['neigh_0', 'map', 'agent'],
        'start_node_id': 0
    },
    'agent_1': {
        'meta': {'team': 0},
        'sensors': ['neigh_1', 'map', 'agent'],
        'start_node_id': 1
    },
    ...
}
```

Here, the keys are the agent names and the values are dictionaries that contain the agent's configuration. The `meta` key contains the metadata of the agent. The `sensors` key contains the list of sensors that the agent has. The `start_node_id` key contains the location id of the node where the agent will start.

A typical `map_strategy` function will look like the following:

```python
def strategy(state):
    # Do something with the state
    state['action'] = (integer) # The location id of the node where the agent will move
    return

def map_strategy(agent_config):
    strategy_map = {}
    for agent_name in agent_config:
        strategy_map[agent_name] = strategy
    return strategy_map
```

In case the user wants to use the agent class, the `map_strategy` function will look like the following:

```python
def map_strategy(agent_config):
    strategy_map = {}
    for agent_name in agent_config:
        strategy_map[agent_name] = Agent(arguements).strategy
    return strategy_map
```

## Random Walk Example

Suppose we have an example game where we want the agents to move randomly. Let's take a quick look at how the game defines the agents and the sensors.

```python
sensor_config = {
    'neigh_0': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
    'neigh_1': {
        'type': gamms.sensor.SensorType.NEIGHBOR,
    },
}

agent_config = {
    'agent_0': {
        'meta': {'team': 0},
        'sensors': ['neigh_0'],
        'start_node_id': 0
    },
    'agent_1': {
        'meta': {'team': 0},
        'sensors': ['neigh_1'],
        'start_node_id': 1
    }
}
```

You can observe that each agent has a neighbor sensor. What that means is that the agent can see the neighbors of the node where it is currently located. The user can define the strategy function as follows:

```python
import random
from gamms import sensor

def strategy(state):
    sensor_data = state['sensor']
    for (type, data) in sensor_data.values():
        if type == sensor.SensorType.NEIGHBOR:
            choice = random.choice(range(len(data)))
            state['action'] = data[choice]
            break
    

def map_strategy(agent_config):
    strategies = {}
    for name in agent_config.keys():
        strategies[name] = strategy
    return strategies
```

In this example, the strategy function randomly chooses a neighbor of the current node and moves to that node. The `map_strategy` function maps the agent names to the strategy functions. The game will use this mapping to run the game.

## A Coverage Example

Suppose we have the exact same game as before but we want the agents to cover the entire graph. The agents do not get information about the entire graph but they can see the neighbors of the node where they are currently located. As such, now we need to remember the nodes that the agents have visited as well as construct the graph from the neighbors. A class based approach is more suitable for this example.

```python
from gamms import sensor
import random

# Shared graph class for all agents
# This is a simple graph class that is used to construct the graph from the neighbors
# It also keeps track of the nodes that have been visited
# The graph is constructed from the neighbors of the nodes
class Graph:
    def __init__(self):
        self.graph = {}
        self.visited = set()

    def add_node(self, node_id, neighbors):
        self.graph[node_id] = neighbors

    def visit(self, node_id):
        self.visited.add(node_id)

    def get_neighbors(self, node_id):
        return self.graph[node_id]

    def get_visited(self):
        return self.visited

# Agent class that uses the graph class
# The agent keeps track of the graph and the visited nodes
# The agent moves to the neighbor that has not been visited
# If all neighbors have been visited, the agent moves to a random neighbor
class Agent:
    def __init__(self, graph):
        self.graph = graph

    def strategy(self, state):
        sensor_data = state['sensor']
        for (type, data) in sensor_data.values():
            if type == sensor.SensorType.NEIGHBOR:
                # Construct the graph
                neighbors = data
                curr_pos = state['curr_pos']
                self.graph.add_node(curr_pos, neighbors)
                visited = self.graph.get_visited()
                unvisited = [node for node in neighbors if node not in visited]
                if len(unvisited) > 0:
                    state['action'] = random.choice(unvisited)
                else:
                    state['action'] = random.choice(neighbors)
                break

# The map_strategy function
# The function creates the graph and the agents
# The agents are then mapped to the strategy functions
def map_strategy(agent_config):
    graph = Graph()
    strategies = {}
    for agent_name in agent_config:
        strategies[agent_name] = Agent(graph).strategy
    return strategies
```

We see that the agents use a common graph object to communicate with each other. This is a simple example of how the agents can share information with each other. However, it should be noted that newer versions of the simulator will provide a more robust way of sharing information between agents via communication sensors. Right now, the implemented policy is a centralized policy where the agents share information with each other via a common object.
