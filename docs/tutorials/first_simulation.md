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

```python title="game.py"
--8<-- "snippets/visualizing_a_grid/square_visualization.py"
```

GAMMS uses a context object to manage the simulation. The context object is created using the `create_context` function. The line below creates a context object with `PYGAME` as the visual engine. The other option we have is `NO_VIS` which is used when we do not want to visualize the simulation.

```python
--8<-- "snippets/visualizing_a_grid/square_visualization.py:4:5"
```

The actual graph object is created inside the context object. Without going into the details, there is a graph manager `ctx.graph` that manages the graph object `ctx.graph.graph`. The graph object is a directed graph that allows us to add nodes and edges to the graph. We use the `add_node` and `add_edge` methods to add nodes and edges to the graph. Each node and edge has an id and some attributes. The id is used to identify the node or edge in the graph. The attributes are used to store information about the node or edge. In this case, we are using the `x` and `y` attributes to store the coordinates of the node in the grid. The `length` attribute is used to store the length of the edge. The length attribute is not directly used in this example andd we will come back to it later. However, it needs to be defined to add the edge to the graph. The `source` and `target` attributes are used the ids of the source and target nodes of the edge.

Once we have added the nodes and edges to the graph, we need to create the graph visualization.

```python
--8<-- "snippets/visualizing_a_grid/square_visualization.py:27:27"
```

We do this using the `set_graph_visual` method of the visual engine. We pass extra parameters to the method to set the width and height of the visualization but these are optional. The default values are 1280 and 720 respectively. The `set_graph_visual` method returns a graph artist object that is used to draw the graph. We will discuss more about artists in later tutorials. The good part is, we do not need to worry about handling the drawing of the graph or what exactly the artist is doing to get started.

The last part of the code is a loop that runs for 120 seconds. The loop calls the `simulate` method of the visual engine to draw the graph. You will now see a window with the square. You can scroll the mouse to zoom in and out of the graph, and use the `WASD` keys to move around the graph. The simulation will run for 120 seconds and then exit automatically.

![Simple Square Grid](images/simple_square_grid.png)
*A simple 2x2 square grid visualization shown in the GAMMS window*

Before moving to the next part, let's make a bigger grid and make it an `n x n` grid. We will create a function that will create a grid of size `n x n` and add it to the graph. The function will take the size of the grid as an argument and create the nodes and edges for the grid. The function will be called `create_grid` and will look like this:

```python
--8<-- "snippets/visualizing_a_grid/nxn_square_visualization.py:9:26"
```

It is usually a good idea to separate out the parameters from the code so that we can easily change them later. We will create a file called `config.py` in the `gammstutorial` directory and add the parameters to this file. The `config.py` file will look like this:

```python title="config.py"
--8<-- "snippets/visualizing_a_grid/config_nxn.py"
```

We have not only added the grid size, but also some other constants or configurations that we had hardcoded in the `game.py` file. The final `game.py` file will look like this:

```python title="game.py"
--8<-- "snippets/visualizing_a_grid/nxn_square_visualization.py"
```

![NxN Grid](images/nxn_grid.png)
*A larger n×n grid visualization with the size defined in config.py*

!!! info "Final changes in the files can be found in [snippets/visualizing_a_grid](https://github.com/GAMMSim/gamms/tree/dev/snippets/visualizing_a_grid)"

## Creating Agents

GAMMS provides a specialized agent class that is used to create agents in the simulation. The agents are limited to the graph and can only move along the edges of the graph. The `ctx.agent.create_agent` call allows us to define an agent in the simulation. The agent needs to have a unique `name` along with information about where it is at the start of the simulation.

Adding the following code to the `game.py`file before the while loop, it will create an agent at the start of the simulation:

```python
--8<-- "snippets/creating_agents/single_agent.py:33:34"
```

The `start_node_id` parameter is the id of the node where the agent will start. The agent will be created at the node with id 0. For making the agent visible in the simulation, we need to also define a visualization for the agent. The agent visualization is created using the `set_agent_visual` method of the visual engine.

```python
--8<-- "snippets/creating_agents/single_agent.py:42:44"
```

<!-- ![Single Agent](images/single_agent.png)
*A single agent displayed on the grid at node 0* -->

You will notice that the agent is not doing anything in the simulation and is just sitting at the start node. The agent is not moving because we have not defined any behaviour for the agent. Let's try to first get human input to move the agent around. The visual engine provides a way to get user input while displaying possible actions on the screen. We need to edit the while loop to get user input:

```python
--8<-- "snippets/creating_agents/single_agent.py:46:60"
```

If you copy the code and replace the while loop in the `game.py` file with this code, the simulation will crash. This is because we have not defined any way for the agent to *sense* the environment. The agent can technically move *blindly* but to show the possible actions, the agent needs to know what the possible actions are. To do this, we need to add a sensor to the agent. Particularly, human input is tied to the `NeighborSensor` and it is reuqired to be able to support taking inputs from the user. Before going through how to add a sensor, let's first understand the changes we made to the while loop. After that, we will go through a simple example of how to add a sensor to the agent, and see how it works.

We have replaced the time based termination to a counter based termination criteria. This is a simple way to simulate *steps* in a game. It also allows a flexible amount of time to be spent on each step. The next thing we are doing is getting the state of the agent. The state of the agent is a dictionary that contains information about the agent. The `get_state` method of the agent returns the state of the agent. We are then using the `human_input` method of the visual engine to get user input for the agent. The `human_input` method takes the name of the agent and its state as arguments and returns the node id where the agent should move. We are then updating the state of the agent with the action taken by the user. The `set_state` method of the agent sets the state of the agent. The important part is that the agent movement is tied to the `action` key in the state dictionary.

Let's now add the `NeighborSensor` to the agent. The `NeighborSensor` is a sensor that senses the neighbors of the agent. It is used to get the possible actions for the agent. The `NeighborSensor` is created using the `create_sensor` method of the agent. The `create_sensor` method takes the name of the sensor and its type as arguments. The type of the sensor is `gamms.sensor.NeighborSensor`. We will add the following code to the `game.py` file after creating the agent:

```python title="game.py"
--8<-- "snippets/creating_agents/single_agent.py:36:40"
```

There are two parts to this code. The first part creates the sensor and the second part registers the sensor to the agent. The `create_sensor` method of the context creates a sensor with the given id and type. The `register_sensor` method of the agent registers the sensor to the agent. When the `get_state` method of the agent is called, the sensor information is updated and added to the state of the agent. The `human_input` method of the visual engine uses this information to show the possible actions for the agent. You will see that the agent is highlighted and you can see some numbers on the nearby nodes. The correspoding number can be pressed on the keyboard to move the agent to that node. The agent will move to the node and you can see the agent moving around the grid.

![Agent With Sensor](images/agent_with_sensor.gif)
*Agent with NeighborSensor showing numbered actions for player input*

!!! info "The maximum number of neighbors that can be handled by human input method is 10. The restriction is only for the human input method and not the sensor itself. The sensor can handle any number of neighbors. The human input method will only show the first 10 neighbors and the rest will be ignored. The human input method will also not show the neighbors if there are more than 10 neighbors. This is a limitation of the current implementation and will be fixed in future releases."

Now that we have a base idea of how to add a single agent, let us try to generalize to two agent teams that we can control. Let us make a Red team and a Blue team, each with 5 agents. The base idea is to do multiple calls to the `create_agent` method using a loop. To make it clean, let us shift some of the configurations to `config.py` file.

```python title="config.py"
--8<-- "snippets/creating_agents/config_multi_agent.py"
```

There are many things to note in the above code. First, we have made the grid size larger to accommodate the agents and the simulation time is now in terms of steps. The number of agents in each team is also defined in the config file. The `sensor_config` dictionary contains the sensor configuration for `NeighborSensor` for each agent. The `agent_config` dictionary contains the agent configuration for each agent. The `meta` key is extra information about the agent that can be used during initialization. The `sensors` key is a list of sensors that are registered to the agent. This way, we do not need to register the sensors to the agent manually. We are storing the each agent's visualization configuration in the `agent_vis_config` dictionary. With all these dictionaries, we can now easily define the agents and their sensors in the `game.py` file like this:

```python
--8<-- "snippets/creating_agents/multi_agent.py:33:44"
```

![Multiple Agents](images/multiple_agents.png)
*Red and blue team agents positioned on the grid according to their configurations*

We have switched the sequence of sensor definition and agent creation. The sensors are created first so that the when the `create_agent` method is called, the method tries to automatically register the sensors to the agent. But if the sensors are not created, the agent will not be able to register the sensors. So, we need to create the sensors first and then create the agents. We can always do the registration manually but it is easier to do it directly.

!!! info "Final changes in the files can be found in [snippets/creating_agents](https://github.com/GAMMSim/gamms/tree/dev/snippets/creating_agents)"

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
--8<-- "snippets/creating_rules/game.py:96:98"
```

The above rule is a simple termination rule we can use to implement the conditioned termination criteria. We have `max_steps` as a global variable which we can set to 120 at the start of the simulation. The `termination_rule` function checks if the step counter is greater than or equal to the maximum number of steps or the maximum simulation steps. We can add `MAX_SIM_STEPS` to the `config.py` file and set it to 1000. The `termination_rule` function will be called in the main loop to check if the simulation should be terminated.

```python title="config.py"
--8<-- "snippets/creating_rules/config.py:7:7"
```

To write the tag rule, we need to check if two agents from opposite teams are on the same node. We have the team in `meta` attribute in agent configuration.

```python title="game.py"
--8<-- "snippets/creating_rules/game.py:46:61"
```

The `tag_rule` function checks if two agents from opposite teams are on the same node. If they are, the agents are reset to their starting positions. The starting positions are stored in the `red_start_dict` and `blue_start_dict` dictionaries. The `current_node_id` attribute of the agent is used to get the current position of the agent. The `current_node_id` attribute is updated to the starting position of the agent. The `prev_node_id` attribute is used to store the previous position of the agent. We also reset it as we are completely resetting the agent to its starting condition.

The `capture_rule` function is similar to the `tag_rule` function. It checks if a blue agent reaches any red agents' starting position. If it does, the blue team gets a point. The same applies for red agents too. The `capture_rule` function looks like this:

```python title="game.py"
--8<-- "snippets/creating_rules/game.py:65:93"
```

![Gameplay](images/gameplay_screenshot.gif)

*Gameplay showing the tag and capture rules in action*

The `capture_rule` function checks if a blue agent reaches any red agents' starting position. If it does, the blue team gets a point. The same applies for red agents too. We are updating the `red_team_score` and `blue_team_score` variables to keep track of the score. The `max_steps` variable is updated to increase the maximum number of steps by 10 on every capture from either team.

Let's put it all in the `game.py` file and  update the main loop to call the rules.

```python title="game.py"
--8<-- "snippets/creating_rules/game.py:1:2"

# ...

--8<-- "snippets/creating_rules/game.py:26:26"

# ...

--8<-- "snippets/creating_rules/game.py:46:47"

# ...

--8<-- "snippets/creating_rules/game.py:96:98"

# ...
--8<-- "snippets/creating_rules/game.py:101:"
```

<!-- ![Game Over Screen](images/game_over.png)
*Game over screen showing the final scores after termination rules are applied* -->

The rules are called after the agent state updates. Note how the capture rule is called before the tag rule. The game rules are actually ambiguous here. Do we first resolve the tag rule and then the capture rule or vice versa? The way we have implemented it, the capture rule is called first and then the tag rule. The example also highlights that the order of rule resolution is important and writing it in this way allows to figure out ambiguities in the rules.

!!! info "Final changes in the files can be found in [snippets/creating_rules](https://github.com/GAMMSim/gamms/tree/dev/snippets/creating_rules)"