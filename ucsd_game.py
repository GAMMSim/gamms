"""
UCSD occlusion test game.
Human-controlled agent on the UCSD walking network with OSM buildings loaded.
Sensor output is printed to terminal each turn.
Close the Pygame window to quit.
"""

import gamms
from gamms import osm as gamms_osm

import math

LOCATION     = "University of California San Diego, La Jolla, CA, USA"
RESOLUTION   = 10.0
SENSOR_RANGE = 80.0
SENSOR_FOV   = math.radians(360)   # 120° cone

# ---------------------------------------------------------------------------
# Load graph
# ---------------------------------------------------------------------------
print("Fetching UCSD walk graph from OSM...")
G = gamms_osm.create_osm_graph(LOCATION, gamms_osm.OSMType.WALK, resolution=RESOLUTION)
print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# ---------------------------------------------------------------------------
# Create context and attach graph
# ---------------------------------------------------------------------------
ctx = gamms.create_context(
    graph_engine=gamms.graph.Engine.MEMORY,
    vis_engine=gamms.visual.Engine.PYGAME,
    vis_kwargs={"width": 1600, "height": 900},
)
ctx.graph.attach_networkx_graph(G)

# ---------------------------------------------------------------------------
# Load buildings
# ---------------------------------------------------------------------------
print("Fetching UCSD buildings from OSM (may take ~30s)...")
face_count = 0
for face in gamms_osm.obstacle_from_osm(LOCATION):
    ctx.graph.add_obstacle_face(
        face["face_id"],
        tr=face["tr"],
        tl=face["tl"],
        br=face["br"],
        bl=face["bl"],
        type=face["type"],
    )
    face_count += 1
print(f"  {face_count} building wall faces loaded")

# ---------------------------------------------------------------------------
# Sensors + agent
# ---------------------------------------------------------------------------
start_node = next(ctx.graph.graph.get_nodes())

ctx.sensor.create_sensor("neighbor", gamms.sensor.SensorType.NEIGHBOR)
ctx.sensor.create_sensor(
    "arc",
    gamms.sensor.SensorType.ARC,
    sensor_range=SENSOR_RANGE,
    fov=SENSOR_FOV,
)
ctx.sensor.create_sensor(
    "occ_map",
    gamms.sensor.SensorType.OCCLUDED_MAP,
    sensor_range=SENSOR_RANGE,
    fov=SENSOR_FOV,
)

ctx.agent.create_agent("player", sensors=["neighbor", "arc", "occ_map"], start_node_id=start_node)
ctx.sensor.get_sensor("arc").set_owner("player")
ctx.sensor.get_sensor("occ_map").set_owner("player")

# ---------------------------------------------------------------------------
# Visuals
# ---------------------------------------------------------------------------
ctx.visual.set_graph_visual()
ctx.visual.set_obstacle_visual()
ctx.visual.set_agent_visual("player", color="blue", size=10)
ctx.visual.set_sensor_visual("arc",     node_color=(255, 200, 0),   edge_color=(200, 160, 0))
ctx.visual.set_sensor_visual("occ_map", node_color=(0,   220, 220), edge_color=(0,   180, 180))

# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------
print("\n=== Game started ===\n")

turn = 0
while not ctx.is_terminated():
    agent = ctx.agent.get_agent("player")
    state = agent.get_state()

    arc_data  = state["sensor"]["arc"][1]
    occ       = state["sensor"]["occ_map"][1]
    arc_nodes = arc_data.get("nodes", {})
    vis_nodes = occ.get("nodes", {})
    neighbors = state["sensor"]["neighbor"][1]
    hidden    = len(arc_nodes) - len(vis_nodes)

    turn += 1
    print(f"Turn {turn:>3} | node {agent.current_node_id:>6} "
          f"| arc: {len(arc_nodes):>4}  occluded: {len(vis_nodes):>4}  hidden by buildings: {hidden:>4} "
          f"| neighbors: {sorted(neighbors)}")

    next_node = ctx.visual.human_input("player", state)
    state["action"] = next_node
    agent.set_state()

    ctx.visual.simulate()

ctx.terminate()
print("Game over.")
