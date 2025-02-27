
# Programming Your First GAMMS Game

## Introduction

This case study walks through setting up a **GAMMS** game from scratch. By following this guide, you will:

✅ Configure a **graph-based environment** using `config.py`.  
✅ Implement **agent strategies** in `blue_strategy.py` (human-controlled) and `red_strategy.py` (AI-controlled).  
✅ Run the **game simulation** using `game.py`.  

By the end, you'll have a **working adversarial simulation** where agents interact in a structured environment.

---

## Step 1: Configuring the Game (`config.py`)

The `config.py` file sets up the **game environment**, including:  
- **Graph settings**  
- **Agent configurations**  
- **Sensor definitions**  
- **Visualization settings**  

### **Configuration Code**
```python
import gamms

# Visualization Engine
vis_engine = gamms.visual.Engine.PYGAME

# Graph Configuration
location = "Sample Area"
resolution = 100.0
graph_path = 'graph.pkl'

# Sensor Configuration
sensor_config = {
    'neigh_0': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_1': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_2': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_3': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_4': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_5': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_6': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_7': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_8': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'neigh_9': {'type': gamms.sensor.SensorType.NEIGHBOR},
    'map': {'type': gamms.sensor.SensorType.MAP},
    'agent': {'type': gamms.sensor.SensorType.AGENT},
}

# Agent Configuration For Two Teams
agent_config = {
    'agent_0': {'meta': {'team': 0}, 'sensors': ['neigh_0', 'map', 'agent'], 'start_node_id': 0},
    'agent_1': {'meta': {'team': 0}, 'sensors': ['neigh_1', 'map', 'agent'], 'start_node_id': 1},
    'agent_2': {'meta': {'team': 0}, 'sensors': ['neigh_2', 'map', 'agent'], 'start_node_id': 2},
    'agent_3': {'meta': {'team': 0}, 'sensors': ['neigh_3', 'map', 'agent'], 'start_node_id': 3},
    'agent_4': {'meta': {'team': 0}, 'sensors': ['neigh_4', 'map', 'agent'], 'start_node_id': 4},
    'agent_5': {'meta': {'team': 1}, 'sensors': ['neigh_5', 'map', 'agent'], 'start_node_id': 500},
    'agent_6': {'meta': {'team': 1}, 'sensors': ['neigh_6', 'map', 'agent'], 'start_node_id': 501},
    'agent_7': {'meta': {'team': 1}, 'sensors': ['neigh_7', 'map', 'agent'], 'start_node_id': 502},
    'agent_8': {'meta': {'team': 1}, 'sensors': ['neigh_8', 'map', 'agent'], 'start_node_id': 503},
    'agent_9': {'meta': {'team': 1}, 'sensors': ['neigh_9', 'map', 'agent'], 'start_node_id': 504},
}

# Visualization Configuration
graph_vis_config = {'width': 1980, 'height': 1080}

agent_vis_config = {
    **{f'agent_{i}': {'color': 'blue', 'size': 8} for i in range(0, 5)},  # Blue Team
    **{f'agent_{i}': {'color': 'red', 'size': 8} for i in range(500, 505)},  # Red Team
}
```

---

## Step 2: Implementing Agent Behavior

Each team follows a different **strategy**:  
- **Blue agents are human-controlled** (no AI strategy).  
- **Red agents use AI for movement decisions**.  

### **Blue Strategy (`blue_strategy.py`)**
Since Blue agents are **human-controlled**, we do not assign them an AI strategy.

```python
def map_strategy(agent_config):
    return {}  # No AI strategy for human-controlled players
```

### **Red Strategy (`red_strategy.py`)**
Red agents follow a **random movement strategy**, choosing a **neighboring node** at each turn.

```python
import random
from gamms import sensor

def strategy(state):
    sensor_data = state['sensor']
    for (sensor_type, neighbors) in sensor_data.values():
        if sensor_type == sensor.SensorType.NEIGHBOR:
            state['action'] = random.choice(neighbors)
            break

def map_strategy(agent_config):
    return {name: strategy for name in agent_config.keys()}
```

---

## Step 3: Running the Simulation (`game.py`)

The `game.py` script:  
✅ Initializes the **game environment**.  
✅ Loads the **graph-based map**.  
✅ Creates and assigns **sensors** to agents.  
✅ Registers **strategies** to agents.  
✅ Runs the **simulation loop** until termination.

### **Game Execution Code**
```python
import gamms
import pickle
from config import (
    vis_engine,
    graph_path,
    sensor_config,
    agent_config,
    graph_vis_config,
    agent_vis_config,
)
import blue_strategy
import red_strategy

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

# Assign strategies: Blue is human-controlled, Red has AI
strategies = red_strategy.map_strategy(agent_config)

# Register strategies for agents
for agent in ctx.agent.create_iter():
    agent.register_strategy(strategies.get(agent.name, None))  # Blue agents get None (manual control)

# Set visualization configurations
ctx.visual.set_graph_visual(**graph_vis_config)

for name, config in agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **config)

#Termination Condition
turn_count = 0

def rule_terminate(ctx):
    global turn_count
    turn_count += 1
    if turn_count > 100:
        ctx.terminate()

# Run the simulation
while not ctx.is_terminated():
    for agent in ctx.agent.create_iter():
        if agent.strategy is not None:
            agent.step()  # AI-controlled agent moves
        else:
            state = agent.get_state()
            node = ctx.visual.human_input(agent.name, state)  # Human-controlled input
            state['action'] = node
            agent.set_state()

    # Update visualization
    ctx.visual.simulate()
    rule_terminate(ctx)
```

---

## Conclusion

By following this structured approach, we successfully implemented a **basic adversarial game** in GAMMS. We:  
✅ Defined a **graph-based environment** for agents to explore.  
✅ Implemented **human-controlled (Blue) and AI-controlled (Red) agents**.  
✅ Ran a **game simulation** with interactive visualization.  

Want to extend this? Try:  
✅ Creating an **AI-controlled Blue Team** for training scenarios.  
✅ Adding **new sensor types** for richer decision-making.  
✅ Implementing **custom agent behaviors** beyond random movement.  

Start modifying your game today! 🚀
