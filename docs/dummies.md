# Programming your first GAMMS game

Welcome to the **GAMMS** example guide! This documentation will walk you through creating and understanding the essential files needed to set up a sample adversarial game using **GAMMS**. Specifically, we'll cover:

- [`config.py`](#configpy)
- [`blue_strategy.py`](#blue_strategypy)
- [`red_strategy.py`](#red_strategypy)
- [`game.py`](#gamepy)

By the end of this guide, you'll have a clear understanding of how to configure your game environment, define agent strategies, and run the simulation.

## Table of Contents

1. [config.py](#configpy)
2. [blue_strategy.py](#blue_strategypy)
3. [red_strategy.py](#red_strategypy)
4. [game.py](#gamepy)

---

## config.py

The `config.py` file defines the configuration settings for your game. This includes visualization settings, sensor configurations, agent configurations, and more.

### Structure and Components

Here's a breakdown of the key sections in `config.py`:

### 1. Imports

```python
import gamms
```

- **gamms**: Imports the **Gamms** library to access necessary classes and enums.

### 2. Visualization Engine

```python
vis_engine = gamms.visual.Engine.PYGAME
```

- **vis_engine**: Sets the visualization engine to `PYGAME`. **Gamms** supports multiple visualization engines; choose the one that fits your needs.

### 3. Graph Configuration

```python
location = "West Point, New York, USA"
resolution = 100.0
graph_path = 'graph.pkl'
```

- **location**: Specifies the real-world location the graph represents.
- **resolution**: Determines the granularity of the graph.
- **graph_path**: Path to the serialized graph file.

### 4. Sensor Configuration

```python
sensor_config = {
    'neigh_0': {'type': gamms.sensor.SensorType.NEIGHBOR},
    ...
    'neigh_9': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'map': {'type': gamms.sensor.SensorType.MAP},
    'agent': {'type': gamms.sensor.SensorType.AGENT},
}
```

- **sensor_config**: Defines various sensors available to agents.
  - Each sensor has a unique name and a type (e.g., `NEIGHBOR`, `MAP`, `AGENT`).
  - More sensors may be added in future versions
### 5. Agent Configuration

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
    ....
    'agent_8': {
        'meta': {'team': 1},
        'sensors': ['neigh_8', 'map', 'agent'],
        'start_node_id': 503
    },
    'agent_9': {
        'meta': {'team': 1},
        'sensors': ['neigh_9', 'map', 'agent'],
        'start_node_id': 504
    }
}
```
- **agent_config**: Defines each agent with:
  - **meta**: Metadata such as team affiliation.
  - **sensors**: List of sensors the agent uses.
  - **start_node_id**: The node where the agent starts on the graph.


### 6. Visualization Configuration

```python

graph_vis_config = {
    'width' : 1980,
    'height' : 1080
}

agent_vis_config = {
    'agent_0': {
        'color': 'blue',
        'size': 8,
    },
    'agent_1': {
        'color': 'blue',
        'size': 8,
    },
    'agent_2': {
        'color': 'blue',
        'size': 8,
    },
    ....
    'agent_8': {
        'color': 'red',
        'size': 8,
    },
    'agent_9': {
        'color': 'red',
        'size': 8,
    }
}
```

- **graph_vis_config**: Sets the dimensions of the visualization window.
- **agent_vis_config**: Defines visual properties for each agent, such as color and size.

### Customization Tips

- **Adding Sensors**: To add more sensors, define them in the `sensor_config` dictionary with unique names and appropriate types.
- **Configuring Agents**: Add or modify agents in the `agent_config` dictionary. Ensure each agent has a unique name, assigned team, sensors, and a valid `start_node_id`.
- **Visualization Settings**: Adjust `graph_vis_config` and `agent_vis_config` to change how the graph and agents appear during simulation.

---

## Strategies 
To see how to build strategies, see strategy.md

## blue_strategy.py

The `blue_strategy.py` file defines the strategy logic for agents on the Blue team. This strategy determines how Blue agents behave based on sensor data.

### Contents of `blue_strategy.py`
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

### Breakdown of the Strategy

1. **Imports**

    ```python
    import random
    from gamms import sensor
    ```

    - **random**: Used for making random decisions.
    - **gamms.sensor**: Provides access to sensor types.

2. **`strategy` Function**

    ```python
    def strategy(state):
        sensor_data = state['sensor']
        for (type, data) in sensor_data.values():
            if type == sensor.SensorType.NEIGHBOR:
                choice = random.choice(range(len(data)))
                state['action'] = data[choice]
                break
    ```

    - **Parameters**:
        - `state`: A dictionary containing the agent's current state, including sensor data.
    - **Logic**:
        - Iterates through sensor data.
        - Identifies sensors of type `NEIGHBOR`.
        - Randomly selects an action from the available neighbor data.
        - Updates the agent's `action` in the state.

3. **`map_strategy` Function**

    ```python
    def map_strategy(agent_config):
        strategies = {}
        for name in agent_config.keys():
            strategies[name] = strategy
        return strategies
    ```

    - **Parameters**:
        - `agent_config`: Configuration dictionary for agents.
    - **Logic**:
        - Maps each agent's name to the `strategy` function.
        - Returns a dictionary of strategies keyed by agent names.

### Customization Tips

- **Strategy Logic**: Modify the `strategy` function to implement different behaviors. For example, prioritize certain actions over others or incorporate more complex decision-making processes.
- **Assigning Strategies**: Ensure that each Blue agent in `agent_config` is mapped to the desired strategy function.

---

## red_strategy.py

The `red_strategy.py` file defines the strategy logic for agents on the Red team. Similar to `blue_strategy.py`, it determines how Red agents behave based on sensor data.

### Contents of `red_strategy.py`

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

### Breakdown of the Strategy

**Note**: The current `red_strategy.py` is identical to `blue_strategy.py`. This setup provides a foundation that can be customized to differentiate behaviors between teams.

### Customization Tips

- **Differentiating Strategies**: To create distinct behaviors for Red agents, modify the `strategy` function. For example, Red agents could prioritize moving towards certain nodes or avoiding specific areas.
- **Advanced Behaviors**: Incorporate additional logic based on other sensor types or environmental factors to create more sophisticated strategies for Red agents.

---
## game.py

The `game.py` script orchestrates the game simulation. It initializes the game context, loads the graph, creates sensors and agents, assigns strategies, and runs the simulation loop.

### Detailed Breakdown

1. **Imports**

    ```python
    import gamms
    from config import (
        vis_engine,
        graph_path,
        sensor_config,
        agent_config,
        graph_vis_config,
        agent_vis_config
    )
    import blue_strategy
    import red_strategy

    import pickle
    ```

    - **gamms**: Core library for game simulation.
    - **config**: Imports all configuration settings.
    - **blue_strategy & red_strategy**: Imports strategy modules for respective teams.
    - **pickle**: Used for loading the serialized graph.

2. **Creating the Game Context**

    ```python
    ctx = gamms.create_context(vis_engine=vis_engine)
    ```

    - Initializes the game context with the specified visualization engine.

3. **Loading the Graph**

    ```python
    with open(graph_path, 'rb') as f:
        G = pickle.load(f)

    ctx.graph.attach_networkx_graph(G)
    ```

    - Loads the graph from a pickle file.
    - Attaches the graph to the game context using NetworkX.

4. **Creating Sensors**

    ```python
    for name, sensor in sensor_config.items():
        ctx.sensor.create_sensor(name, sensor['type'], **sensor.get('args', {}))
    ```

    - Iterates through `sensor_config` to create each sensor in the context.

5. **Creating Agents**

    ```python
    for name, agent in agent_config.items():
        ctx.agent.create_agent(name, **agent)
    ```

    - Iterates through `agent_config` to create each agent in the context.

6. **Assigning Strategies**

    ```python
    strategies = {}

    # Blue is human so do not set strategy
    # strategies.update(blue_strategy.map_strategy(
    #     {name: val for name, val in agent_config.items() if val['meta']['team'] == 0}
    # ))

    strategies.update(red_strategy.map_strategy(
        {name: val for name, val in agent_config.items() if val['meta']['team'] == 1}
    ))
    ```

    - **Blue Team**: Currently commented out, implying Blue agents are controlled by human input.
    - **Red Team**: Assigns the Red team strategy to Red agents.

7. **Registering Strategies**

    ```python
    for agent in ctx.agent.create_iter():
        agent.register_strategy(strategies.get(agent.name, None))
    ```

    - Registers the appropriate strategy with each agent. Agents without a strategy (e.g., Blue agents) can be controlled manually.

8. **Setting Visualization Configurations**

    ```python
    ctx.visual.set_graph_visual(**graph_vis_config)

    for name, config in agent_vis_config.items():
        ctx.visual.set_agent_visual(name, **config)
    ```

    - Applies graph and agent visualization settings from the configuration.

9. **Adding Special Nodes**

    ```python
    n1 = ctx.graph.graph.get_node(0)
    n2 = ctx.graph.graph.get_node(1)
    data = {}
    data['x'] = n1.x
    data['y'] = n1.y
    data['scale'] = 10.0
    data['color'] = (255, 0, 0)

    ctx.visual.add_artist('special_node', data)
    ```

    - Highlights specific nodes (`n1` and `n2`) with visual markers.

10. **Game Rules and Mechanics**

    - **Turn Count and Termination**

        ```python
        turn_count = 0

        def rule_terminate(ctx):
            global turn_count
            turn_count += 1
            if turn_count > 100:
                ctx.terminate()
        ```

        - Increments the turn count each loop and terminates the game after 100 turns.

    - **Agent Reset Logic**

        ```python
        def agent_reset(ctx):
            blue_agent_pos = {}
            red_agent_pos = {}
            for agent in ctx.agent.create_iter():
                if agent.meta['team'] == 0:
                    blue_agent_pos[agent.name] = agent.current_node_id
                else:
                    red_agent_pos[agent.name] = agent.current_node_id
            for blue_agent in blue_agent_pos:
                for red_agent in red_agent_pos:
                    if blue_agent_pos[blue_agent] == red_agent_pos[red_agent]:
                        ctx.agent.get_agent(red_agent).current_node_id = 0
        ```

        - Resets Red agents to node `0` if they collide with any Blue agent.

    - **Valid Step Check**

        ```python
        def valid_step(ctx):
            for agent in ctx.agent.create_iter():
                state = agent.get_state()
                sensor_name = agent_config[agent.name]['sensors'][0]
                if agent.current_node_id not in state[sensor_name]:
                    agent.current_node_id = agent.prev_node_id
        ```

        - Ensures agents are moving to valid nodes based on sensor data.

11. **Simulation Loop**

    ```python
    while not ctx.is_terminated():
        for agent in ctx.agent.create_iter():
            if agent.strategy is not None:
                agent.step()
            else:
                state = agent.get_state()
                node = ctx.visual.human_input(agent.name, state)
                state['action'] = node
                agent.set_state()

        # valid_step(ctx)
        # agent_reset(ctx)
        if turn_count % 2 == 0:
            data['x'] = n1.x
            data['y'] = n1.y
        else:
            data['x'] = n2.x
            data['y'] = n2.y
        ctx.visual.simulate()

        # ctx.save_frame()
        rule_terminate(ctx)
    ```

    - **Agent Actions**:
        - Agents with strategies execute their `step()` method.
        - Agents without strategies (e.g., Blue agents) receive human input for actions.
    - **Visualization Update**:
        - Alternates the position of the `special_node` between `n1` and `n2` each turn.
        - Calls `ctx.visual.simulate()` to update the visualization.
    - **Game Termination**:
        - Invokes `rule_terminate(ctx)` to check if the game should end.
### Final File
### Contents of `game.py`

```python
import gamms
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config
)
import blue_strategy
import red_strategy

import pickle

# Create the game context
ctx = gamms.create_context(vis_engine=vis_engine)

# Load the graph
with open(graph_path, 'rb') as f:
    G = pickle.load(f)

ctx.graph.attach_networkx_graph(G)

# Create the sensors
for name, sensor in sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor.get('args', {}))

# Create the agents
for name, agent in agent_config.items():
    ctx.agent.create_agent(name, **agent)

# Create the strategies
strategies = {}

# Blue is human so do not set strategy
# strategies.update(blue_strategy.map_strategy(
#     {name: val for name, val in agent_config.items() if val['meta']['team'] == 0}
# ))

strategies.update(red_strategy.map_strategy(
    {name: val for name, val in agent_config.items() if val['meta']['team'] == 1}
))

# Set the strategies
for agent in ctx.agent.create_iter():
    agent.register_strategy(strategies.get(agent.name, None))

# Set visualization configurations
ctx.visual.set_graph_visual(**graph_vis_config)

# Set agent visualization configurations
for name, config in agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **config)

# Special nodes
n1 = ctx.graph.graph.get_node(0)
n2 = ctx.graph.graph.get_node(1)
data = {}
data['x'] = n1.x
data['y'] = n1.y
data['scale'] = 10.0
data['color'] = (255, 0, 0)

ctx.visual.add_artist('special_node', data)

turn_count = 0

# Rules for the game
def rule_terminate(ctx):
    global turn_count
    turn_count += 1
    if turn_count > 100:
        ctx.terminate()

def agent_reset(ctx):
    blue_agent_pos = {}
    red_agent_pos = {}
    for agent in ctx.agent.create_iter():
        if agent.meta['team'] == 0:
            blue_agent_pos[agent.name] = agent.current_node_id
        else:
            red_agent_pos[agent.name] = agent.current_node_id
    for blue_agent in blue_agent_pos:
        for red_agent in red_agent_pos:
            if blue_agent_pos[blue_agent] == red_agent_pos[red_agent]:
                ctx.agent.get_agent(red_agent).current_node_id = 0

def valid_step(ctx):
    for agent in ctx.agent.create_iter():
        state = agent.get_state()
        sensor_name = agent_config[agent.name]['sensors'][0]
        if agent.current_node_id not in state[sensor_name]:
            agent.current_node_id = agent.prev_node_id

# Run the game
while not ctx.is_terminated():
    for agent in ctx.agent.create_iter():
        if agent.strategy is not None:
            agent.step()
        else:
            state = agent.get_state()
            node = ctx.visual.human_input(agent.name, state)
            state['action'] = node
            agent.set_state()

    # valid_step(ctx)
    # agent_reset(ctx)
    if turn_count % 2 == 0:
        data['x'] = n1.x
        data['y'] = n1.y
    else:
        data['x'] = n2.x
        data['y'] = n2.y
    ctx.visual.simulate()

    # ctx.save_frame()
    rule_terminate(ctx)
```

### Customization Tips

- **Adding Game Rules**: Implement additional functions to enforce specific game rules, such as scoring, victory conditions, or environmental changes.
- **Extending Agent Behavior**: Enhance the simulation loop with more complex interactions between agents or environmental factors.
- **Visualization Enhancements**: Customize the visualization further by adding more artists, adjusting visual properties dynamically, or integrating different visualization engines.

---

## Final Steps

### 1. Clone or Download the `examples` Directory

Clone or download the `examples` directory from the [GAMMSim/gamms](https://github.com/GAMMSim/gamms/tree/main/examples) repository and place it inside your project directory:

```sh
git clone https://github.com/GAMMSim/gamms.git
mv gamms/examples examples
rm -rf gamms
```

Alternatively, using `wget`:

```sh
wget https://github.com/GAMMSim/gamms/archive/refs/heads/main.zip
unzip main.zip
mv gamms-main/examples examples
rm -rf gamms-main main.zip
```

### 2. Create the `games` Folder and Strategy Files

As detailed above, ensure that the `games` folder contains `blue_strategy.py`, `red_strategy.py`, `config.py`, and `game.py`.

### 3. Verify Installation

Activate your virtual environment and verify the installation:

```sh
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate     # Windows

python
```

In the Python shell, run:

```python
import gamms
print("Gamms version:", gamms.__version__)
```

You should see the installed Gamms version printed, confirming a successful installation.

### 4. Run the Game

With everything set up, you can run your game simulation:

```sh
python games/game.py
```

This will start the simulation based on your configurations and strategies.

---

## Using a Code Workspace

To manage and edit your project efficiently, consider using a code editor like **Visual Studio Code (VS Code)**. Here's how to set it up:

1. **Install VS Code**: If you haven't already, download and install [Visual Studio Code](https://code.visualstudio.com/).

2. **Open Your Project**:
   - Launch VS Code.
   - Click on `File` > `Open Folder...` and select your `gamms` project directory.

3. **Set Up Python Environment in VS Code**:
   - Install the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) for VS Code.
   - VS Code should automatically detect your virtual environment. If not, you can select it manually by clicking on the Python version in the status bar and choosing the appropriate interpreter from the `venv` folder.

4. **Navigate and Edit Files**:
   - Use the Explorer pane on the left to navigate through your project files.
   - Open and edit `config.py`, `blue_strategy.py`, `red_strategy.py`, and `game.py` as needed.

5. **Run and Debug**:
   - You can run your game directly from the terminal in VS Code.
   - Use breakpoints and the debugging tools to step through your code.

---

## Summary

By following the steps above, you can set up your **Gamms** project with the necessary configuration and strategy files. Here's a quick recap:

- **Project Structure**: Organized directories and files for easy management.
- **Configuration Files**: `config.py` sets up sensors, agents, and visualization.
- **Strategy Files**: `blue_strategy.py` and `red_strategy.py` define agent behaviors.
- **Game Orchestration**: `game.py` initializes and runs the simulation.
- **Documentation**: `start.md` and `raw.md` provide guidance and explanations.
- **Workspace Setup**: Using VS Code or another code editor for efficient development.

Feel free to customize the strategies, configurations, and game rules to suit your specific simulation needs. If you have any further questions or need additional assistance, feel free to ask!

Happy coding and simulating!