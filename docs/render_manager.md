# Render Manager

The purpose of `RenderManager` is to provide unified draw call APIs and handles the drawing of all artists(or `render_node`). The `RenderManager` class is used by `pygame_engine` as an extension to the pygame visualization engine.  
The functions of `RenderManager` includes:
- Provides static draw function that can be used in custom drawers.
- Manages the drawing of all `render_node`.
- Handles the drawing of graph and agents.

## Render Node
`RenderNode` is an object defined and used internally in `RenderManager` to draw one or more visuals in the scene. It contains a dictionary data that's defined by the user. Some data in this dictionary are used internally to define the behaviour of the `RenderNode`, here are a list of them:
- `drawer`: This should be None or a custom function that will handle all drawings of this render node. The function should takes context and data as arguments, where context is the current context of the game and data is the data dictionary of this render node. Note that if the `drawer` exists in render node data, it is expected to override the entire renderings for this node and none of the render method will be called internally.
- `shape`: This is used to select internal render function if the render node does not have a `drawer`. It must be the type of `VisualizationEngine.Shape`.
- `x`: This is the x coordinate in world space, used when drawing simple shapes.
- `y`: This is the y coordinate in world space, used when drawing simple shapes.
- `color`: This is the color of the render node, only used when drawing simple shapes.

### Simple Shapes
Here is a list of possible shapes and attributes they used:
- `Circle`: a solid circle, uses `x`, `y` for position, `color` for color, and `scale` for radius.
- `Graph`: this is only used by default graph render node, it uses a single data `graph` that is the type of `IGraph`.
- `Agent`: this is only used by default agent render node, each agent will have its render node. It uses a single data `agent_visual` that is the type of `AgentVisual`.

## Helper Render Functions
There are some helper render functions in `RenderManager`, their purpose is to provide an easy way to draw elements on screen when you use custom drawer. These functions are also used to draw simple shapes internally. All of these functions are static and take context as the first argument.
Here are a list of functions:
```python
@staticmethod
def render_circle(ctx: Context, x: float, y: float, radius: float, color: tuple=Color.Black):
    """
    Render a circle at the given position with the given radius and color.

    Args:
        ctx (Context): The current simulation context.
        x (float): The x coordinate of the circle's center.
        y (float): The y coordinate of the circle's center.
        radius (float): The radius of the circle.
        color (tuple, optional): The color the the circle. Defaults to Color.Black.
    """
    pass

@staticmethod
def render_graph(ctx: Context, graph: IGraph):
    """
    Render the graph by drawing its nodes and edges on the screen. This is the default rendering method for graphs.

    Args:
        ctx (Context): The current simulation context.
        graph (IGraph): The graph to render.
    """
    pass

@staticmethod
def render_agent(ctx: Context, agent_visual: AgentVisual):
    """
    Render an agent as a triangle at its current position on the screen. This is the default rendering method for agents.

    Args:
        ctx (Context): The current simulation context.
        agent_visual (AgentVisual): The visual representation of the agent to render.
    """
    pass
```

---
::: gamms.VisualizationEngine.RenderManager
    options:
        show_source: false
        heading_level: 4