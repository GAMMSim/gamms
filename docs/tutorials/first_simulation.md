---
title: First Simulation
---

# Writing your First Simulation

Our goal in this tutorial is to start developing a simple grid world simulation with GAMMS. We will extend this example in coming tutorials to introduce the various features of GAMMS as well as flesh out a complex scenario at the end of all the tutorials. The goal of this tutorial is to get you familiar with the basic concepts of GAMMS and how to use it to create a simple simulation.

First, we need to create a project directory. This is where we will store all our simulation files. The  project directory can be anywhere on your computer but for keeping things together we will create a directory called `gammstutorial` in the virtual environment we created in the installation tutorial.

We will be completely working in this directory so make sure you are in the right place. Ensure you have activated the virtual environment before running any files that we create and always be in the `gammstutorial` directory when running the files. You can check if you are in the right directory by running the following command:

```sh
pwd
```

## Visualizing a Grid

Create a file called `game.py` in the `gammstutorial` directory. This file is the entry point for our simulation. Copy the following code into the file:

<!-- square_visualization.py -->

```python
import time
import gamms

ctx = gamms.create_context(vis_engine=gamms.visual.Engine.PYGAME) # create a context with PYGAME as the visual engine

graph = ctx.graph.graph # get the graph object from the context

# Create a 1x1 grid

graph.add_node({'id': 0, 'x': 0, 'y': 0}) # add a node to the graph with id 0 and coordinates (0, 0)
graph.add_node({'id': 1, 'x': 100.0, 'y': 0}) # add a node to the graph with id 1 and coordinates (1, 0)
graph.add_node({'id': 2, 'x': 100.0, 'y': 100.0}) # add a node to the graph with id 2 and coordinates (0, 1)
graph.add_node({'id': 3, 'x': 0, 'y': 100.0}) # add a node to the graph with id 3 and coordinates (1, 1)
graph.add_edge({'id': 0, 'source': 0, 'target': 1, 'length': 1.0}) # add an edge to the graph with id 0 from node 0 to node 1
graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1.0}) # add an edge to the graph with id 1 from node 1 to node 2
graph.add_edge({'id': 2, 'source': 2, 'target': 3, 'length': 1.0}) # add an edge to the graph with id 2 from node 2 to node 3
graph.add_edge({'id': 3, 'source': 3, 'target': 0, 'length': 1.0}) # add an edge to the graph with id 3 from node 3 to node 0
graph.add_edge({'id': 4, 'source': 0, 'target': 3, 'length': 1.0}) # add an edge to the graph with id 4 from node 0 to node 3
graph.add_edge({'id': 5, 'source': 3, 'target': 2, 'length': 1.0}) # add an edge to the graph with id 5 from node 3 to node 2
graph.add_edge({'id': 6, 'source': 2, 'target': 1, 'length': 1.0}) # add an edge to the graph with id 6 from node 2 to node 1
graph.add_edge({'id': 7, 'source': 1, 'target': 0, 'length': 1.0}) # add an edge to the graph with id 7 from node 1 to node 0


# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(width=1980, height=1080) # set the graph visualization with width 1980 and height 1080

t = time.time() # get the current time
while time.time() - t < 120: # run the loop for 120 seconds
    ctx.visual.simulate() # Draw loop for the visual engine

ctx.terminate() # terminate the context
```

GAMMS uses a context object to manage the simulation. The context object is created using the `create_context` function. The line below creates a context object with `PYGAME` as the visual engine. The other option we have is `NO_VIS` which is used when we do not want to visualize the simulation.

```python
ctx = gamms.create_context(vis_engine=gamms.visual.Engine.PYGAME) # create a context with PYGAME as the visual engine
```

The actual graph object is created inside the context object. Without going into the details, there is a graph manager `ctx.graph` that manages the graph object `ctx.graph.graph`. The graph object is a directed graph that allows us to add nodes and edges to the graph. We use the `add_node` and `add_edge` methods to add nodes and edges to the graph. Each node and edge has an id and some attributes. The id is used to identify the node or edge in the graph. The attributes are used to store information about the node or edge. In this case, we are using the `x` and `y` attributes to store the coordinates of the node in the grid. The `length` attribute is used to store the length of the edge. The length attribute is not directly used in this example andd we will come back to it later. However, it needs to be defined to add the edge to the graph. The `source` and `target` attributes are used the ids of the source and target nodes of the edge.

Once we have added the nodes and edges to the graph, we need to create the graph visualization.

```python
graph_artist = ctx.visual.set_graph_visual(width=1980, height=1080) # set the graph visualization with width 1980 and height 1080
```

We do this using the `set_graph_visual` method of the visual engine. We pass extra parameters to the method to set the width and height of the visualization but these are optional. The default values are 1280 and 720 respectively. The `set_graph_visual` method returns a graph artist object that is used to draw the graph. We will discuss more about artists in later tutorials. The good part is, we do not need to worry about handling the drawing of the graph or what exactly the artist is doing to get started.

The last part of the code is a loop that runs for 120 seconds. The loop calls the `simulate` method of the visual engine to draw the graph. You will now see a window with the square. You can scroll the mouse to zoom in and out of the graph, and use the `WASD` keys to move around the graph. The simulation will run for 120 seconds and then exit automatically.


Before moving to the next part, let's make a bigger grid and make it an `n x n` grid. We will create a function that will create a grid of size `n x n` and add it to the graph. The function will take the size of the grid as an argument and create the nodes and edges for the grid. The function will be called `create_grid` and will look like this:

```python
def create_grid(graph, n):
    edge_count = 0 # initialize the edge count to 0
    for i in range(n):
        for j in range(n):
            graph.add_node({'id': i * n + j, 'x': i * 100.0, 'y': j * 100.0}) # add a node to the graph with id i * n + j and coordinates (i, j)
            if i > 0:
                graph.add_edge({'id': edge_count, 'source': (i - 1) * n + j, 'target': i * n + j, 'length': 1.0}) # add an edge to the graph from node (i - 1) * n + j to node i * n + j
                # Opposite direction
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': (i - 1) * n + j, 'length': 1.0}) # add an edge to the graph from node i * n + j to node (i - 1) * n + j
                edge_count += 2 # increment the edge count by 2
            if j > 0:
                graph.add_edge({'id': edge_count, 'source': i * n + (j - 1), 'target': i * n + j, 'length': 1.0}) # add an edge to the graph from node i * n + (j - 1) to node i * n + j
                # Opposite direction
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': i * n + (j - 1), 'length': 1.0}) # add an edge to the graph from node i * n + j to node i * n + (j - 1)
                edge_count += 2 # increment the edge count by 2
```

It is usually a good idea to separate out the parameters from the code so that we can easily change them later. We will create a file called `config.py` in the `gammstutorial` directory and add the parameters to this file. The `config.py` file will look like this:

```python title="config.py"
import gamms


VIS_ENGINE = gamms.visual.Engine.PYGAME # visual engine to use
GRID_SIZE = 5 # size of the grid

SIM_TIME = 120 # time to run the simulation in seconds

graph_vis_config = {
    'width': 1980, # width of the graph visualization
    'height': 1080, # height of the graph visualization
}
```

We have not only added the grid size, but also some other constants or configurations that we had hardcoded in the `game.py` file. The final `game.py` file will look like this:

```python title="game.py"
import time
import gamms
import config

ctx = gamms.create_context(vis_engine=config.VIS_ENGINE) # create a context with PYGAME as the visual engine

graph = ctx.graph.graph # get the graph object from the context

# Create a 1x1 grid

def create_grid(graph, n):
    edge_count = 0 # initialize the edge count to 0
    for i in range(n):
        for j in range(n):
            graph.add_node({'id': i * n + j, 'x': i * 100.0, 'y': j * 100.0}) # add a node to the graph with id i * n + j and coordinates (i, j)
            if i > 0:
                graph.add_edge({'id': edge_count, 'source': (i - 1) * n + j, 'target': i * n + j, 'length': 1.0}) # add an edge to the graph from node (i - 1) * n + j to node i * n + j
                # Opposite direction
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': (i - 1) * n + j, 'length': 1.0}) # add an edge to the graph from node i * n + j to node (i - 1) * n + j
                edge_count += 2 # increment the edge count by 2
            if j > 0:
                graph.add_edge({'id': edge_count, 'source': i * n + (j - 1), 'target': i * n + j, 'length': 1.0}) # add an edge to the graph from node i * n + (j - 1) to node i * n + j
                # Opposite direction
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': i * n + (j - 1), 'length': 1.0}) # add an edge to the graph from node i * n + j to node i * n + (j - 1)
                edge_count += 2 # increment the edge count by 2

create_grid(graph, config.GRID_SIZE)


# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(**config.graph_vis_config) # set the graph visualization with width 1980 and height 1080

t = time.time() # get the current time
while time.time() - t < config.SIM_TIME: # run the loop for 120 seconds
    ctx.visual.simulate() # Draw loop for the visual engine

ctx.terminate() # terminate the context
```

## Creating Agents

GAMMS provides a specialized agent class that is used to create agents in the simulation. The agents are limited to the graph and can only move along the edges of the graph. The `ctx.agent.create_agent` call allows us to define an agent in the simulation. The agent needs to have a unique `name` along with information about where it is at the start of the simulation.

Adding the following code to the `game.py`file before the while loop, it will create an agent at the start of the simulation:

```python
# Create an agent
ctx.agent.create_agent(name='agent_0', start_node_id=0)
```

The `start_node_id` parameter is the id of the node where the agent will start. The agent will be created at the node with id 0. For making the agent visible in the simulation, we need to also define a visualization for the agent. The agent visualization is created using the `set_agent_visual` method of the visual engine.

```python
# Create the agent visualization
# set the agent visualization with name 'agent_0', color red and size 10
ctx.visual.set_agent_visual(name='agent_0', color=(255, 0, 0), size=10)
```

You will notice that the agent is not doing anything in the simulation and is just sitting at the start node. The agent is not moving because we have not defined any behaviour for the agent. Let's try to first get human input to move the agent around. The visual engine provides a way to get user input while displaying possible actions on the screen. We need to edit the while loop to get user input:

```python
step_counter = 0 # initialize the step counter to 0
while not ctx.is_terminated(): # run the loop until the context is terminated
    step_counter += 1 # increment the step counter by 1
    for agent in ctx.agent.create_iter():
        # Get the current state of the agent
        state = agent.get_state() # get the state of the agent
        # Get human input to move the agent
        node = ctx.visual.human_input(agent.name, state)
        state['action'] = node
        agent.set_state() # set the state of the agent
    

    ctx.visual.simulate() # Draw loop for the visual engine
    if step_counter == 20:
        ctx.terminate() # terminate the context after 20 steps
```

If you copy the code and replace the while loop in the `game.py` file with this code, the simulation will crash. This is because we have not defined any way for the agent to *sense* the environment. The agent can technically move *blindly* but to show the possible actions, the agent needs to know what the possible actions are. To do this, we need to add a sensor to the agent. Particularly, human input is tied to the `NeighborSensor` and it is reuqired to be able to support taking inputs from the user. Before going through how to add a sensor, let's first understand the changes we made to the while loop. After that, we will go through a simple example of how to add a sensor to the agent, and see how it works.

We have replaced the time based termination to a counter based termination criteria. This is a simple way to simulate *steps* in a game. It also allows a flexible amount of time to be spent on each step. The next thing we are doing is getting the state of the agent. The state of the agent is a dictionary that contains information about the agent. The `get_state` method of the agent returns the state of the agent. We are then using the `human_input` method of the visual engine to get user input for the agent. The `human_input` method takes the name of the agent and its state as arguments and returns the node id where the agent should move. We are then updating the state of the agent with the action taken by the user. The `set_state` method of the agent sets the state of the agent. The important part is that the agent movement is tied to the `action` key in the state dictionary.

Let's now add the `NeighborSensor` to the agent. The `NeighborSensor` is a sensor that senses the neighbors of the agent. It is used to get the possible actions for the agent. The `NeighborSensor` is created using the `create_sensor` method of the agent. The `create_sensor` method takes the name of the sensor and its type as arguments. The type of the sensor is `gamms.sensor.NeighborSensor`. We will add the following code to the `game.py` file after creating the agent:

```python
# Create a neighbor sensor
ctx.sensor.create_sensor(sensor_id='neigh_0', sensor_type=gamms.sensor.SensorType.NEIGHBOR)

# Register the sensor to the agent
ctx.agent.get_agent('agent_0').register_sensor(name='neigh_0', sensor=ctx.sensor.get_sensor('neigh_0'))
```

There are two parts to this code. The first part creates the sensor and the second part registers the sensor to the agent. The `create_sensor` method of the context creates a sensor with the given id and type. The `register_sensor` method of the agent registers the sensor to the agent. When the `get_state` method of the agent is called, the sensor information is updated and added to the state of the agent. The `human_input` method of the visual engine uses this information to show the possible actions for the agent. You will see that the agent is highlighted and you can see some numbers on the nearby nodes. The correspoding number can be pressed on the keyboard to move the agent to that node. The agent will move to the node and you can see the agent moving around the grid.

*The maximum number of neighbors that can be handled by human input method is 10. The restriction is only for the human input method and not the sensor itself. The sensor can handle any number of neighbors. The human input method will only show the first 10 neighbors and the rest will be ignored. The human input method will also not show the neighbors if there are more than 10 neighbors. This is a limitation of the current implementation and will be fixed in future releases.*

The final `game.py` file will look like this:

```python title="game.py"
import gamms
import config

ctx = gamms.create_context(vis_engine=config.VIS_ENGINE) # create a context with PYGAME as the visual engine

graph = ctx.graph.graph # get the graph object from the context

def create_grid(graph, n):
    edge_count = 0 # initialize the edge count to 0
    for i in range(n):
        for j in range(n):
            graph.add_node({'id': i * n + j, 'x': i * 100.0, 'y': j * 100.0}) # add a node to the graph with id i * n + j and coordinates (i, j)
            if i > 0:
                # add an edge to the graph from node (i - 1) * n + j to node i * n + j
                graph.add_edge({'id': edge_count, 'source': (i - 1) * n + j, 'target': i * n + j, 'length': 1.0})
                # add an edge to the graph from node i * n + j to node (i - 1) * n + j
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': (i - 1) * n + j, 'length': 1.0})
                edge_count += 2 # increment the edge count by 2
            if j > 0:
                # add an edge to the graph from node i * n + (j - 1) to node i * n + j
                graph.add_edge({'id': edge_count, 'source': i * n + (j - 1), 'target': i * n + j, 'length': 1.0})
                # add an edge to the graph from node i * n + j to node i * n + (j - 1)
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': i * n + (j - 1), 'length': 1.0})
                edge_count += 2 # increment the edge count by 2

create_grid(graph, config.GRID_SIZE)


# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(**config.graph_vis_config) # set the graph visualization with width 1980 and height 1080

# Create an agent
ctx.agent.create_agent(name='agent_0', start_node_id=0)

# Create a neighbor sensor
ctx.sensor.create_sensor(sensor_id='neigh_0', sensor_type=gamms.sensor.SensorType.NEIGHBOR)

# Register the sensor to the agent
ctx.agent.get_agent('agent_0').register_sensor(name='neigh_0', sensor=ctx.sensor.get_sensor('neigh_0'))

# Create the agent visualization
# set the agent visualization with name 'agent_0', color red and size 10
ctx.visual.set_agent_visual(name='agent_0', color=(255, 0, 0), size=10)

step_counter = 0 # initialize the step counter to 0
while not ctx.is_terminated(): # run the loop until the context is terminated
    step_counter += 1 # increment the step counter by 1
    for agent in ctx.agent.create_iter():
        # Get the current state of the agent
        state = agent.get_state() # get the state of the agent
        # Get human input to move the agent
        node = ctx.visual.human_input(agent.name, state)
        state['action'] = node
        agent.set_state() # set the state of the agent
    

    ctx.visual.simulate() # Draw loop for the visual engine
    if step_counter == 20:
        ctx.terminate() # terminate the context after 20 steps

ctx.terminate() # terminate the context
```

Now that we have a base idea of how to add a single agent, let us try to generalize to two agent teams that we can control. Let us make a Red team and a Blue team, each with 5 agents. The base idea is to do multiple calls to the `create_agent` method using a loop. To make it clean, let us shift some of the configurations to `config.py` file.

```python title="config.py"
import gamms


VIS_ENGINE = gamms.visual.Engine.PYGAME # visual engine to use
GRID_SIZE = 20 # size of the grid

SIM_STEPS = 120 # NUMBER OF STEPS IN THE SIMULATION

RED_TEAM_AGENTS = 10 # NUMBER OF AGENTS IN THE RED TEAM
BLUE_TEAM_AGENTS = 10 # NUMBER OF AGENTS IN THE BLUE TEAM

graph_vis_config = {
    'width': 1980, # width of the graph visualization
    'height': 1080, # height of the graph visualization
}

sensor_config = {}

for i in range(RED_TEAM_AGENTS + BLUE_TEAM_AGENTS):
    sensor_config[f'neigh_{i}'] = {
        'type': gamms.sensor.SensorType.NEIGHBOR, # type of the sensor
    }

agent_config = {}

for i in range(RED_TEAM_AGENTS):
    agent_config[f'agent_{i}'] = {
        'meta': {'team': 0}, # team of the agent
        'sensors': [f'neigh_{i}'], # sensors of the agent
        'start_node_id': i, # starting node id of the agent
    }

for i in range(RED_TEAM_AGENTS, RED_TEAM_AGENTS + BLUE_TEAM_AGENTS):
    agent_config[f'agent_{i}'] = {
        'meta': {'team': 1}, # team of the agent
        'sensors': [f'neigh_{i}'], # sensors of the agent
        'start_node_id': 400-1-i, # starting node id of the agent
    }

agent_vis_config = {}

for i in range(RED_TEAM_AGENTS):
    agent_vis_config[f'agent_{i}'] = {
        'color': (255, 0, 0), # color of the agent
        'size': 10, # size of the agent
    }

for i in range(RED_TEAM_AGENTS, RED_TEAM_AGENTS + BLUE_TEAM_AGENTS):
    agent_vis_config[f'agent_{i}'] = {
        'color': (0, 0, 255), # color of the agent
        'size': 10, # size of the agent
    }

```

There are many things to note in the above code. First, we have made the grid size larger to accommodate the agents and the simulation time is now in terms of steps. The number of agents in each team is also defined in the config file. The `sensor_config` dictionary contains the sensor configuration for `NeighborSensor` for each agent. The `agent_config` dictionary contains the agent configuration for each agent. The `meta` key is extra information about the agent that can be used during initialization. The `sensors` key is a list of sensors that are registered to the agent. This way, we do not need to register the sensors to the agent manually. We are storing the each agent's visualization configuration in the `agent_vis_config` dictionary. With all these dictionaries, we can now easily define the agents and their sensors in the `game.py` file like this:

```python title="game.py"
# Create all the sensors
for name, sensor in config.sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor)

# Create all the agents
for name, agent in config.agent_config.items():
    ctx.agent.create_agent(name, **agent)


# Create all agents visualization
for name, vis_config in config.agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **vis_config)
```

We have switched the sequence of sensor definition and agent creation. The sensors are created first so that the when the `create_agent` method is called, the method tries to automatically register the sensors to the agent. But if the sensors are not created, the agent will not be able to register the sensors. So, we need to create the sensors first and then create the agents. We can always do the registration manually but it is easier to do it directly.


## Creating Scenario Rules

Now that we have set up the agents and the environment, we need to define the rules of the scenario. We already have implcitly defined a rule by defining the termination based on turn count. Rules in GAMMS are defined directly in the `game` file. These rules are simple definitions that can directly mutate the game state. An easy way to define a rule is to create a function that takes the context as an argument and do condition checks. The way these rules actually come into play is by actually calling the function in the main loop, giving full control in which order the rules apply.

Let us try to implement the following rules:

1. The game will run for atleast 120 steps and at most 1000 steps.
2. If two agents of opposite teams are on the same node, they will be reset to their starting positions. Lets call this the *tag* rule.
3. If a blue agent reaches any red agents' starting position, blue team will get a point. Lets call this the *capture* rule.
4. The capture applies for red agents too. If a red agent reaches any blue agents' starting position, red team will get a point.
5. On a capture, the agent will be reset to its starting position.
6. On every capture, the maximum number of steps will be increased by 10 steps (added to 120 with a cap of 1000).
7. Maximum point team wins.


```python title="game.py"
def termination_rule(ctx):
    if step_counter >= max_steps or step_counter >= config.MAX_SIM_STEPS:
        ctx.terminate()
```

The above rule is a simple termination rule we can use to implement the conditioned termination criteria. We have `max_steps` as a global variable which we can set to 120 at the start of the simulation. The `termination_rule` function checks if the step counter is greater than or equal to the maximum number of steps or the maximum simulation steps. We can add `MAX_SIM_STEPS` to the `config.py` file and set it to 1000. The `termination_rule` function will be called in the main loop to check if the simulation should be terminated.

```python title="config.py"
MAX_SIM_STEPS = 1000 # maximum number of steps in the simulation
```

To write the tag rule, we need to check if two agents from opposite teams are on the same node. We have the team in `meta` attribute in agent configuration.

```python title="game.py"
red_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 0]
blue_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 1]
red_start_dict = {name: config.agent_config[name]['start_node_id'] for name in red_team}
blue_start_dict = {name: config.agent_config[name]['start_node_id'] for name in blue_team}

def tag_rule(ctx):
    for red_agent in red_team:
        for blue_agent in blue_team:
            ragent = ctx.agent.get_agent(red_agent)
            bagent = ctx.agent.get_agent(blue_agent)
            if ragent.current_node_id == bagent.current_node_id:
                # Reset the agents to their starting positions
                ragent.current_node_id = red_start_dict[red_agent]
                bagent.current_node_id = blue_start_dict[blue_agent]
                ragent.prev_node_id = red_start_dict[red_agent]
                bagent.prev_node_id = blue_start_dict[blue_agent]
```

The `tag_rule` function checks if two agents from opposite teams are on the same node. If they are, the agents are reset to their starting positions. The starting positions are stored in the `red_start_dict` and `blue_start_dict` dictionaries. The `current_node_id` attribute of the agent is used to get the current position of the agent. The `current_node_id` attribute is updated to the starting position of the agent. The `prev_node_id` attribute is used to store the previous position of the agent. We also reset it as we are completely resetting the agent to its starting condition.

The `capture_rule` function is similar to the `tag_rule` function. It checks if a blue agent reaches any red agents' starting position. If it does, the blue team gets a point. The same applies for red agents too. The `capture_rule` function looks like this:

```python title="game.py"
red_team_score = 0
blue_team_score = 0
max_steps = 120

def capture_rule(ctx):
    global max_steps
    global red_team_score
    global blue_team_score
    for red_agent in red_team:
        agent = ctx.agent.get_agent(red_agent)
        for val in blue_start_dict.values():
            if agent.current_node_id == val:
                # Red team gets a point
                red_team_score += 1
                # Reset the agent to its starting position
                agent.current_node_id = red_start_dict[red_agent]
                agent.prev_node_id = red_start_dict[red_agent]
                max_steps += 10
    
    for blue_agent in blue_team:
        agent = ctx.agent.get_agent(blue_agent)
        for val in red_start_dict.values():
            if agent.current_node_id == val:
                # Blue team gets a point
                blue_team_score += 1
                # Reset the agent to its starting position
                agent.current_node_id = blue_start_dict[blue_agent]
                agent.prev_node_id = blue_start_dict[blue_agent]
                max_steps += 10
```

The `capture_rule` function checks if a blue agent reaches any red agents' starting position. If it does, the blue team gets a point. The same applies for red agents too. We are updating the `red_team_score` and `blue_team_score` variables to keep track of the score. The `max_steps` variable is updated to increase the maximum number of steps by 10 on every capture from either team.

Let's put it all in the `game.py` file and  update the main loop to call the rules. The final `game.py` file will look like this:

```python title="game.py"
import gamms
import config

ctx = gamms.create_context(vis_engine=config.VIS_ENGINE) # create a context with PYGAME as the visual engine

graph = ctx.graph.graph # get the graph object from the context

def create_grid(graph, n):
    edge_count = 0 # initialize the edge count to 0
    for i in range(n):
        for j in range(n):
            graph.add_node({'id': i * n + j, 'x': i * 100.0, 'y': j * 100.0}) # add a node to the graph with id i * n + j and coordinates (i, j)
            if i > 0:
                # add an edge to the graph from node (i - 1) * n + j to node i * n + j
                graph.add_edge({'id': edge_count, 'source': (i - 1) * n + j, 'target': i * n + j, 'length': 1.0})
                # add an edge to the graph from node i * n + j to node (i - 1) * n + j
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': (i - 1) * n + j, 'length': 1.0})
                edge_count += 2 # increment the edge count by 2
            if j > 0:
                # add an edge to the graph from node i * n + (j - 1) to node i * n + j
                graph.add_edge({'id': edge_count, 'source': i * n + (j - 1), 'target': i * n + j, 'length': 1.0})
                # add an edge to the graph from node i * n + j to node i * n + (j - 1)
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': i * n + (j - 1), 'length': 1.0})
                edge_count += 2 # increment the edge count by 2

create_grid(graph, config.GRID_SIZE)

# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(**config.graph_vis_config) # set the graph visualization with width 1980 and height 1080

# Create all the sensors
for name, sensor in config.sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor)

# Create all the agents
for name, agent in config.agent_config.items():
    ctx.agent.create_agent(name, **agent)


# Create all agents visualization
for name, vis_config in config.agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **vis_config)


red_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 0]
blue_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 1]
red_start_dict = {name: config.agent_config[name]['start_node_id'] for name in red_team}
blue_start_dict = {name: config.agent_config[name]['start_node_id'] for name in blue_team}    print("Environment created")


def tag_rule(ctx):
    for red_agent in red_team:
        for blue_agent in blue_team:
            ragent = ctx.agent.get_agent(red_agent)
            bagent = ctx.agent.get_agent(blue_agent)
            if ragent.current_node_id == bagent.current_node_id:
                # Reset the agents to their starting positions
                ragent.current_node_id = red_start_dict[red_agent]
                bagent.current_node_id = blue_start_dict[blue_agent]
                ragent.prev_node_id = red_start_dict[red_agent]
                bagent.prev_node_id = blue_start_dict[blue_agent]



red_team_score = 0
blue_team_score = 0
max_steps = 120

def capture_rule(ctx):
    global max_steps
    global red_team_score
    global blue_team_score
    for red_agent in red_team:
        agent = ctx.agent.get_agent(red_agent)
        for val in blue_start_dict.values():
            if agent.current_node_id == val:
                # Red team gets a point
                red_team_score += 1
                # Reset the agent to its starting position
                agent.current_node_id = red_start_dict[red_agent]
                agent.prev_node_id = red_start_dict[red_agent]
                max_steps += 10
    
    for blue_agent in blue_team:
        agent = ctx.agent.get_agent(blue_agent)
        for val in red_start_dict.values():
            if agent.current_node_id == val:
                # Blue team gets a point
                blue_team_score += 1
                # Reset the agent to its starting position
                agent.current_node_id = blue_start_dict[blue_agent]
                agent.prev_node_id = blue_start_dict[blue_agent]
                max_steps += 10


def termination_rule(ctx):
    if step_counter >= max_steps or step_counter >= config.MAX_SIM_STEPS:
        ctx.terminate()


step_counter = 0 # initialize the step counter to 0
while not ctx.is_terminated(): # run the loop until the context is terminated
    step_counter += 1 # increment the step counter by 1
    for agent in ctx.agent.create_iter():
        # Get the current state of the agent
        state = agent.get_state() # get the state of the agent
        # Get human input to move the agent
        node = ctx.visual.human_input(agent.name, state)
        state['action'] = node
        agent.set_state() # set the state of the agent
    

    ctx.visual.simulate() # Draw loop for the visual engine
    capture_rule(ctx) # check capture rule
    tag_rule(ctx) # check tag rule
    termination_rule(ctx) # check termination rule

ctx.terminate() # terminate the context
```

The rules are called after the agent state updates. Note how the capture rule is called before the tag rule. The game rules are actually ambiguous here. Do we first resolve the tag rule and then the capture rule or vice versa? The way we have implemented it, the capture rule is called first and then the tag rule. The example also highlights that the order of rule resolution is important and writing it in this way allows to figure out ambiguities in the rules.
