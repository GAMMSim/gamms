import gamms, gamms.osm
import config

ctx = gamms.create_context(
    vis_engine=gamms.visual.Engine.PYGAME,
    vis_kwargs={'simulation_time_constant': 0.3},
    logger_config={'level': 'WARNING'},
) # create a context with PYGAME as the visual engine

G = gamms.osm.graph_from_xml(
    config.XML_FILE,
    resolution=config.RESOLUTION,
    tolerance=config.TOLERANCE,
    bidirectional=config.BIDIRECTIONAL
)
ctx.graph.attach_networkx_graph(G) # attach the graph to the context

# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(**config.graph_vis_config) # set the graph visualization with width 1980 and height 1080

# Create all agents visualization
for name, vis_config in config.agent_vis_config.items():
    artist = ctx.visual.set_agent_visual(name, **vis_config)

for _ in ctx.record.replay("recording"):
    continue

ctx.terminate() # terminate the context