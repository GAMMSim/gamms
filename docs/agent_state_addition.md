
# Passing Extra Information to Agent States in GAMMS

## Introduction

GAMMS allows you to pass custom information to agents via their state. This feature is particularly useful for enhancing agent strategies with contextual or dynamic data. In this guide, you'll learn how to:
1. Add extra information to an agent's state.
2. Use that information in the agent's strategy.
3. Dynamically update state information during the simulation.

---

## Adding Extra Information to Agent State

You can pass custom variables to an agent's state by using the `state.update()` method. This can be done during each simulation step. This information can then be accessed to create your strategy.

### Example: Adding Custom Variables to State

```python
for agent in ctx.agent.create_iter():
    state = agent.get_state()

    # Add custom variables to the agent's state
    state.update({
        "food_positions": [food['x'] for food in remaining_food],  # Node IDs of food
        "agent_params": {"speed": 5, "energy": 100},               # Custom parameters
        "flag_positions": FLAG_POSITIONS,                         # Example static data
    })

    # Execute the agent's strategy
    agent.strategy(state)

    # Update the state back to the agent
    agent.set_state()
```


## Dynamically Updating State Information

State information can also be updated dynamically during the simulation. For example, you might want to update a variable based on changes in the environment.

### Example: Updating State Based on Agent Interaction

```python
for agent in ctx.agent.create_iter():
    state = agent.get_state()

    # Example: Update energy level based on movement
    if state['action']:
        state['agent_params']['energy'] -= 1

    # Example: Remove a food position if the agent reaches it
    if state['curr_pos'] in state['food_positions']:
        state['food_positions'].remove(state['curr_pos'])

    # Execute the agent's strategy
    agent.strategy(state)

    # Update the state back to the agent
    agent.set_state()
```

---

## Handling Initialization of Custom State Variables

To ensure custom state variables are initialized properly, you can set them during the simulation startup or the first simulation step.

### Example: Initializing State Variables

```python
for agent in ctx.agent.create_iter():
    state = agent.get_state()

    # Initialize custom variables if they don't exist
    if 'memory' not in state:
        state['memory'] = {}  # Initialize memory for tracking visited nodes

    agent.set_state()
```

---

## Advanced Use Case: Sharing Global Data

Sometimes you might want agents to share global information, such as environmental conditions or the positions of other agents.

### Example: Sharing Global Data Among Agents

```python
global_data = {
    "temperature": 25,
    "wind_speed": 10,
    "food_locations": [0, 1, 2, 3],
}

for agent in ctx.agent.create_iter():
    state = agent.get_state()

    # Share global data with agents
    state.update(global_data)

    agent.strategy(state)
    agent.set_state()
```

---
