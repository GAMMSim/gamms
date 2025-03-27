import gamms.AgentEngine.agent_engine as agent
import gamms.SensorEngine.sensor_engine as sensor
import gamms.GraphEngine.graph_engine as graph
import gamms.VisualizationEngine as visual
from gamms.Recorder.recorder import Recorder
from gamms.context import Context
from enum import Enum

from gamms.typing import logger

import logging

import os

def create_context(
    vis_engine: Enum = visual.Engine.NO_VIS,
    vis_kwargs: dict = None,
) -> Context:
    _logger = logging.getLogger("gamms")
    ctx = Context(logger=_logger)
    if vis_kwargs is None:
        vis_kwargs = {}
    if vis_engine == visual.Engine.NO_VIS:
        from gamms.VisualizationEngine import no_engine
        visual_engine = no_engine.NoEngine(ctx, **vis_kwargs)
    elif vis_engine == visual.Engine.PYGAME:
        from gamms.VisualizationEngine import pygame_engine
        visual_engine = pygame_engine.PygameVisualizationEngine(ctx, **vis_kwargs)
    else:
        raise NotImplementedError(f"Visualization engine {vis_engine} not implemented")
    
    graph_engine = graph.GraphEngine(ctx)
    agent_engine = agent.AgentEngine(ctx)
    sensor_engine = sensor.SensorEngine(ctx)
    ctx.agent_engine = agent_engine
    ctx.graph_engine = graph_engine
    ctx.visual_engine = visual_engine
    ctx.sensor_engine = sensor_engine
    ctx.recorder = Recorder(ctx)
    loglevel = os.environ.get("GAMMS_LOG_LEVEL", "INFO").upper()
    if loglevel == "DEBUG":
        ctx.logger.setLevel(logger.DEBUG)
    elif loglevel == "INFO":
        ctx.logger.setLevel(logger.INFO)
    elif loglevel == "WARNING":
        ctx.logger.setLevel(logger.WARNING)
    elif loglevel == "ERROR":
        ctx.logger.setLevel(logger.ERROR)
    elif loglevel == "CRITICAL":
        ctx.logger.setLevel(logger.CRITICAL)
    else:
        ctx.logger.setLevel(logger.INFO)
    ctx.logger.info(f"Setting log level to {ctx.logger.level}")
    ctx.set_alive()
    return ctx