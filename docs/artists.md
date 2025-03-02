# Using Artists in GAMMS

## Introduction

In GAMMS, artists are visual elements that can be added to the simulation to enhance visualization. They are typically used to represent objects like resources, obstacles, or any custom markers. This guide explains how to create, customize, and use artists in your GAMMS simulations.

---

## Creating an Artist

Artists are added using the `ctx.visual.add_artist()` method. This requires you to define:
1. **Name**: A unique identifier for the artist.
2. **Data**: A dictionary containing the artist's properties (e.g., position, color, size).

### Example: Adding a Circle Artist

The following example creates a circle artist to represent a resource on the graph:

```python
# Define the data for the circle artist
circle_data = {
    'x': 100,            # X-coordinate
    'y': 200,            # Y-coordinate
    'scale': 15.0,       # Radius of the circle
    'color': (255, 0, 0) # RGB color (red)
}

# Add the circle artist to the visualization
ctx.visual.add_artist('resource_node', circle_data)
```

---

## Updating Artists Dynamically

Artists can be updated dynamically during the simulation to reflect changes in the environment. For example, you can move a circle to a new position or change its color.

### Example: Updating an Artist's Position

```python
# Update the position of an artist
circle_data['x'] = 150  # New X-coordinate
circle_data['y'] = 250  # New Y-coordinate

# Re-add or update the artist
ctx.visual.add_artist('resource_node', circle_data)
```

---

## Removing an Artist

To remove an artist, use the `ctx.visual.remove_artist()` method with the name of the artist:

```python
# Remove the circle artist
ctx.visual.remove_artist('resource_node')
```

---

## Customizing Artists

Artists can be customized with additional properties to represent various objects in the simulation. Below are some common customizations:

1. **Shape**:
   - Circles (`pygame.draw.circle`) are the default, but you can create custom shapes by extending the artist logic.

2. **Color**:
   - Use RGB tuples like `(255, 0, 0)` for red, `(0, 255, 0)` for green, etc.

3. **Size**:
   - The `scale` property defines the size of the artist (e.g., the radius of a circle).

4. **Dynamic Properties**:
   - Pass any extra data into the `data` dictionary for custom rendering logic.

---

## Advanced Example: Highlighting Nodes Dynamically

In this example, we use artists to highlight nodes as agents visit them:

```python
visited_nodes = set()

while not ctx.is_terminated():
    for agent in ctx.agent.create_iter():
        current_node = agent.current_node_id
        if current_node not in visited_nodes:
            visited_nodes.add(current_node)
            
            # Create a circle to highlight the visited node
            highlight_data = {
                'x': ctx.graph.graph.get_node(current_node).x,
                'y': ctx.graph.graph.get_node(current_node).y,
                'scale': 10.0,
                'color': (0, 255, 0)  # Green color for visited nodes
            }
            ctx.visual.add_artist(f'visited_node_{current_node}', highlight_data)
```

---