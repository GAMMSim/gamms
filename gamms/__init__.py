import gamms.AgentEngine.agent_engine as agent
import gamms.SensorEngine.sensor_engine as sensor
import gamms.GraphEngine.graph_engine as graph
import gamms.VisualizationEngine as visual
from gamms.context import Context
from enum import Enum

def create_context(
    vis_engine: Enum = visual.Engine.NO_VIS,
    vis_kwargs: dict = None,
) -> Context:
    ctx = Context()
    if vis_kwargs is None:
        vis_kwargs = {}
    if vis_engine == visual.Engine.NO_VIS:
        visual_engine = visual.no_engine.NoEngine(ctx, **vis_kwargs)
    elif vis_engine == visual.Engine.PYGAME:
        visual_engine = visual.pygame_engine.PygameVisualizationEngine(ctx, **vis_kwargs)
    else:
        raise NotImplementedError(f"Visualization engine {vis_engine} not implemented")
    
    graph_engine = graph.GraphEngine(ctx)
    agent_engine = agent.AgentEngine(ctx)
    sensor_engine = sensor.SensorEngine(ctx)
    ctx.agent_engine = agent_engine
    ctx.graph_engine = graph_engine
    ctx.visual_engine = visual_engine
    ctx.sensor_engine = sensor_engine
    ctx.set_alive()
    return ctx