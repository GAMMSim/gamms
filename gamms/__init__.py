import gamms.AgentEngine.agent_engine as agent
import gamms.SensorEngine.sensor_engine as sensor
import gamms.GraphEngine.graph_engine as graph
import gamms.VisualizationEngine as visual
from gamms.Recorder.recorder import Recorder
from gamms.context import Context
from enum import Enum

from gamms.typing import logger
from typing import Dict, Any, Optional

import logging

import os

def create_context(
    graph_engine: Enum = graph.Engine.SQLITE,
    vis_engine: Enum = visual.Engine.NO_VIS,
    vis_kwargs: Optional[Dict[str, Any]] = None,
    logger_config: Optional[Dict[str, Any]] = None,
) -> Context:
    _logger = logging.getLogger("gamms")
    if logger_config is None:
        logger_config = {}
    ctx = Context(logger=_logger)
    if vis_kwargs is None:
        vis_kwargs = {}
    if vis_engine == visual.Engine.NO_VIS:
        visual_engine = visual.NoEngine(ctx, **vis_kwargs)
    elif vis_engine == visual.Engine.PYGAME:
        visual_engine = visual.PygameVisualizationEngine(ctx, **vis_kwargs)
    else:
        raise NotImplementedError(f"Visualization engine {vis_engine} not implemented")
    
    agent_engine = agent.AgentEngine(ctx)
    sensor_engine = sensor.SensorEngine(ctx)
    ctx.agent_engine = agent_engine
    ctx.graph_engine = graph.GraphEngine(ctx, engine=graph_engine)
    ctx.visual_engine = visual_engine
    ctx.sensor_engine = sensor_engine
    ctx.recorder = Recorder(ctx)
    loglevel = os.environ.get("GAMMS_LOG_LEVEL", "INFO").upper()
    if loglevel == "DEBUG":
        loglevel = logger.DEBUG
    elif loglevel == "INFO":
        loglevel = logger.INFO
    elif loglevel == "WARNING":
        loglevel = logger.WARNING
    elif loglevel == "ERROR":
        loglevel = logger.ERROR
    elif loglevel == "CRITICAL":
        loglevel = logger.CRITICAL
    else:
        loglevel = logger.INFO
    if "level" not in logger_config:
        logger_config["level"] = loglevel
    
    logging.basicConfig(**logger_config)
    ctx.logger.setLevel(logger_config["level"])
    ctx.logger.info(f"Setting log level to {ctx.logger.level}")
    ctx.set_alive()
    return ctx

__version__ = "0.2.0"