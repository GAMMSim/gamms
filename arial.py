import gamms
import gamms.osm
from gamms.VisualizationEngine import Color
from gamms.typing import AgentType

# Create La Jolla graph
print("Creating La Jolla graph...")
G = gamms.osm.create_osm_graph("La Jolla, San Diego, California, USA", resolution=50.0)
print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

# Create gamms context
print("Setting up visualization...")
ctx = gamms.create_context(vis_engine=gamms.visual.Engine.PYGAME)
ctx.graph.attach_networkx_graph(G)

# Set up graph visualization
ctx.visual.set_graph_visual(
    node_color=Color.DarkGray, 
    edge_color=Color.LightGray,
    node_size=6  # Bigger nodes
)

# Create aerial sensor with downward-facing cone
ctx.sensor.create_sensor(
    'aerial_sensor', 
    gamms.sensor.SensorType.AERIAL,
    sensor_range=200.0,  # 200 meter range
    fov=6.0,  # Field of view in radians (about 60 degrees)
)

# Create aerial agent
ctx.agent.create_agent(
    'drone',
    type=AgentType.AERIAL,
    start_node_id=0,  # Start at first node
    speed=50.0,  # 50 meters per step
    sensors=['aerial_sensor']
)

# Set up agent visualization (smaller cyan drone)
ctx.visual.set_agent_visual(
    'drone',
    color=Color.Cyan,
    size=8  # Smaller drone
)

# Set up sensor visualization (highlight sensed area in green)
ctx.visual.set_sensor_visual(
    'aerial_sensor',
    node_color=Color.Green,
    edge_color=Color.Green
)

# Add ground agents near spawn area
print("Creating ground agents...")
spawn_node = 0
nearby_nodes = [80, 95, 172, 83]  # Get 4 nearby nodes

# Create ground agents
ground_agents = []
for i, node_id in enumerate(nearby_nodes):
    agent_name = f'ground_agent_{i}'
    
    # Create basic ground agent
    ctx.agent.create_agent(
        agent_name,
        start_node_id=node_id,
        sensors=[]  # No sensors needed
    )
    ground_agents.append(agent_name)
    
    # Set up visualization (different colors)
    ctx.visual.set_agent_visual(
        agent_name,
        color=Color.Purple,
        size=10
    )

# Simple strategy for ground agents - stay still
def stay_still_strategy(state):
    # Just stay at current position
    state['action'] = state['curr_pos']

# Register stay-still strategy for all ground agents
for agent_name in ground_agents:
    agent = ctx.agent.get_agent(agent_name)
    agent.register_strategy(stay_still_strategy)

print("Visualization ready!")
print("Controls:")
print("- WASD: Move camera")
print("- Mouse wheel: Zoom")
print("- Press 0: Stop drone")
print("- Click: Move drone to location")
print("- Arrow keys: Move drone up/down")
print("- Close window to exit")
print(f"- {len(ground_agents)} ground agents will stay near spawn area")

# Simple strategy for human control
def human_strategy(state):
    # Get human input for aerial agent
    direction = ctx.visual.human_input('drone', state)
    state['action'] = direction

# Register strategy
drone = ctx.agent.get_agent('drone')
drone.register_strategy(human_strategy)

# Main loop
while not ctx.is_terminated():
    # Update drone (human controlled)
    drone_state = drone.get_state()
    print(drone_state)
    drone.strategy(drone_state)
    drone.set_state()
    
    # Update ground agents (they stay still)
    for agent_name in ground_agents:
        agent = ctx.agent.get_agent(agent_name)
        agent_state = agent.get_state()
        agent.strategy(agent_state)
        agent.set_state()
    
    # Update visualization
    ctx.visual.simulate()