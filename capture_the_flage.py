import gamms
import gamms.osm
import random
import math
from gamms.typing import IContext
from gamms.VisualizationEngine import Color
from gamms.VisualizationEngine.artist import Artist
from gamms import sensor

def create_territory_artist(ctx: IContext, territory_nodes: list, color: tuple, name: str):
    """Create a custom artist to highlight territory with large visible color"""
    def territory_drawer(ctx: IContext, data: dict):
        nodes = data['nodes']
        color = data['color']
        
        # Draw large filled circles on territory nodes for high visibility
        for node_id in nodes:
            node = ctx.graph.graph.get_node(node_id)
            # Large filled circles with semi-transparent color
            alpha_color = (*color[:3], 120)  # Semi-transparent but visible
            ctx.visual.render_circle(node.x, node.y, 25, alpha_color, width=0)  # Filled circle
            # Add border for extra visibility
            ctx.visual.render_circle(node.x, node.y, 25, color, width=3)  # Border
    
    artist = Artist(ctx, territory_drawer, layer=5)
    artist.data['nodes'] = territory_nodes
    artist.data['color'] = color
    return artist

def create_flag_artist(ctx: IContext, node_id: int, flag_color: tuple, name: str):
    """Create a simple SQUARE artist - just a square"""
    def square_drawer(ctx: IContext, data: dict):
        node_id = data['node_id']
        color = data['color']
        
        node = ctx.graph.graph.get_node(node_id)
        x, y = node.x, node.y
        
        # Draw a simple square
        square_size = 20  # Side length
        
        # Draw filled square
        ctx.visual.render_rectangle(x, y, square_size, square_size, color, perform_culling_test=False)
        
        # Draw square outline for visibility using lines
    artist = Artist(ctx, square_drawer, layer=15)
    artist.data['node_id'] = node_id
    artist.data['color'] = flag_color
    return artist

def stationary_strategy(state):
    """Strategy that keeps agents in place - no movement"""
    # Stay at current position
    state['action'] = state['curr_pos']

def main():
    # Create GAMMS context with Pygame visualization
    ctx = gamms.create_context(vis_engine=gamms.visual.Engine.PYGAME)
    
    # Load La Jolla map
    print("Loading La Jolla map...")
    try:
        G = gamms.osm.create_osm_graph("La Jolla, California, USA", resolution=10.0)
        print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    except Exception as e:
        print(f"Error loading map: {e}")
        # Fallback to a simple test map
        print("Using fallback simple graph...")
        import networkx as nx
        G = nx.grid_2d_graph(10, 10)
        # Convert to format expected by gamms
        G_new = nx.Graph()
        for i, (x, y) in enumerate(G.nodes()):
            G_new.add_node(i, x=float(x*100), y=float(y*100))
        for i, (u, v) in enumerate(G.edges()):
            u_idx = list(G.nodes()).index(u)
            v_idx = list(G.nodes()).index(v)
            G_new.add_edge(u_idx, v_idx, id=i, length=100.0)
        G = G_new
    
    # Attach graph to GAMMS
    ctx.graph.attach_networkx_graph(G)
    
    # Set up graph visualization
    ctx.visual.set_graph_visual(
        node_color=Color.DarkGray,
        node_size=2,
        edge_color=Color.LightGray,
        width=1400,
        height=900
    )
    
    # Analyze territories based on node positions
    all_nodes = list(ctx.graph.graph.get_nodes())
    node_positions = [(node_id, ctx.graph.graph.get_node(node_id)) for node_id in all_nodes]
    
    # Find center longitude to split territories
    longitudes = [node.x for _, node in node_positions]
    center_x = sum(longitudes) / len(longitudes)
    
    # Split into territories
    blue_territory = []  # Western side (blue)
    red_territory = []   # Eastern side (red)
    
    for node_id, node in node_positions:
        if node.x <= center_x:
            blue_territory.append(node_id)
        else:
            red_territory.append(node_id)
    
    print(f"Blue territory: {len(blue_territory)} nodes")
    print(f"Red territory: {len(red_territory)} nodes")
    
    # Create territory highlighting artists
    if blue_territory:
        blue_artist = create_territory_artist(ctx, blue_territory, Color.Blue, "blue_territory")
        ctx.visual.add_artist("blue_territory", blue_artist)
    
    if red_territory:
        red_artist = create_territory_artist(ctx, red_territory, Color.Red, "red_territory")
        ctx.visual.add_artist("red_territory", red_artist)
    
    # Find flag positions (extreme points)
    westernmost_node = min(node_positions, key=lambda x: x[1].x)[0]
    easternmost_node = max(node_positions, key=lambda x: x[1].x)[0]
    
    # Create flag artists
    blue_flag = create_flag_artist(ctx, westernmost_node, Color.Blue, "blue_flag")
    ctx.visual.add_artist("blue_flag", blue_flag)
    
    red_flag = create_flag_artist(ctx, easternmost_node, Color.Red, "red_flag")
    ctx.visual.add_artist("red_flag", red_flag)
    
    # Create sensors
    sensors = {}
    for i in range(10):  # 10 agents
        sensor_name = f'neighbor_{i}'
        sensors[sensor_name] = ctx.sensor.create_sensor(
            sensor_name, 
            sensor.SensorType.NEIGHBOR
        )
    
    # Create and place agents randomly
    agents = []
    for i in range(10):
        team = 0 if i < 5 else 1  # First 5 are blue team (0), rest are red team (1)
        
        # Choose random starting position from appropriate territory
        if team == 0 and blue_territory:
            start_node = random.choice(blue_territory)
            color = 'green'  # Team 0 is now green
        elif team == 1 and red_territory:
            start_node = random.choice(red_territory)
            color = 'purple'  # Team 1 is now purple
        else:
            start_node = random.choice(all_nodes)
            color = 'green' if team == 0 else 'purple'
        
        agent_name = f'agent_{i}'
        
        # Create agent
        agent = ctx.agent.create_agent(
            agent_name,
            start_node_id=start_node,
            sensors=[f'neighbor_{i}'],
            meta={'team': team}
        )
        
        # Add stationary strategy - agents won't move
        agent.register_strategy(stationary_strategy)
        
        # Set up agent visualization - MASSIVE SIZE
        ctx.visual.set_agent_visual(
            agent_name,
            color=color,
            size=50  # HUGE agents!
        )
        
        agents.append(agent)
        print(f"Created {agent_name} on node {start_node} (team {team}) - {color.upper()} agent, SIZE 50, STATIONARY")
    
    print(f"\nGame setup complete!")
    print(f"- {len(blue_territory)} blue territory nodes")
    print(f"- {len(red_territory)} red territory nodes") 
    print(f"- {len(agents)} agents created (GREEN vs PURPLE teams)")
    print(f"- Blue SQUARE flag at node {westernmost_node}")
    print(f"- Red SQUARE flag at node {easternmost_node}")
    print("\n🎮 STATIONARY AGENTS:")
    print("- Agents have stationary strategy (won't move)")
    print("- GREEN agents (Team 0) in blue territory")
    print("- PURPLE agents (Team 1) in red territory") 
    print("- Agents are MASSIVE (size 50) with SQUARE FLAGS!")
    print("\nStarting visualization... Close window or press Ctrl+C to exit")
    
    # Game loop - Stationary agents with strategies
    turn_count = 0
    try:
        while not ctx.is_terminated():
            # Move all agents using their stationary strategies
            for agent in ctx.agent.create_iter():
                if agent.strategy is not None:
                    state = agent.get_state()
                    agent.strategy(state)
                    agent.set_state()
            
            # Simulate visualization step
            ctx.visual.simulate()
            turn_count += 1
            
            # Optional: limit turns for screenshot purposes  
            if turn_count > 100:
                print("Game completed 100 turns. Screenshot ready!")
                break
                
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"Game error: {e}")
    finally:
        print("Terminating game...")
        ctx.terminate()

if __name__ == "__main__":
    main()