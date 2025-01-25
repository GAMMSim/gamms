# Render Manager

The purpose of `RenderManager` is to provide unified draw call APIs and handles the drawing of all artists(or `render_node`). The `RenderManager` class is used by `pygame_engine` as an extension to the pygame visualization engine.  
The functions of `RenderManager` includes:
- Provides static draw function that can be used in custom drawers.
- Manages the drawing of all artists(or `render_node`).
- Handles the drawing of graph and agents.

---
::: gamms.VisualizationEngine.RenderManager
    options:
        show_source: false
        heading_level: 4