import gamms, gamms.osm
import config
import random

ctx = gamms.create_context(vis_engine=config.VIS_ENGINE) # create a context with PYGAME as the visual engine

G = gamms.osm.graph_from_xml(config.XML_FILE, resolution=config.RESOLUTION, tolerance=config.TOLERANCE, bidirectional=config.BIDIRECTIONAL)
ctx.graph.attach_networkx_graph(G) # attach the graph to the context

# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(**config.graph_vis_config) # set the graph visualization with width 1980 and height 1080

# Create all the sensors
for name, sensor in config.sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor)

red_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 0]
blue_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 1]

# Start position of the agents
nodes = ctx.graph.graph.nodes
node_keys = list(nodes.keys())
blue_territory = set()
red_territory = set()
for name in red_team:
    start_node = random.choice(node_keys)
    config.agent_config[name]['start_node_id'] = start_node
    node_keys.remove(start_node)
    removes = set()
    for node_id in node_keys:
        if (nodes[start_node].x - nodes[node_id].x)**2 + (nodes[start_node].y - nodes[node_id].y)**2 < config.TERRITORY_RADIUS**2:
            red_territory.add(node_id)
            removes.add(node_id)
    
    for node_id in removes:
        node_keys.remove(node_id)

for name in blue_team:
    start_node = random.choice(node_keys)
    config.agent_config[name]['start_node_id'] = start_node
    node_keys.remove(start_node)
    removes = set()
    for node_id in node_keys:
        if (nodes[start_node].x - nodes[node_id].x)**2 + (nodes[start_node].y - nodes[node_id].y)**2 < config.TERRITORY_RADIUS**2:
            blue_territory.add(node_id)
            removes.add(node_id)
    
    for node_id in removes:
        node_keys.remove(node_id)

red_start_dict = {name: config.agent_config[name]['start_node_id'] for name in red_team}
blue_start_dict = {name: config.agent_config[name]['start_node_id'] for name in blue_team}

# Create all the agents
for name, agent in config.agent_config.items():
    ctx.agent.create_agent(name, **agent)


# Create all agents visualization
for name, vis_config in config.agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **vis_config)

red_team_score = 0
blue_team_score = 0
max_steps = config.MIN_SIM_STEPS

def tag_rule(ctx):
    global red_team_score
    global blue_team_score
    global max_steps
    for red_agent in red_team:
        for blue_agent in blue_team:
            ragent = ctx.agent.get_agent(red_agent)
            bagent = ctx.agent.get_agent(blue_agent)
            if ragent.current_node_id == bagent.current_node_id:
                if ragent.current_node_id in red_territory:
                    # Red team gets a point
                    red_team_score += 1
                    # Reset only the blue agent to its starting position
                    bagent.current_node_id = blue_start_dict[blue_agent]
                    bagent.prev_node_id = blue_start_dict[blue_agent]
                    max_steps += config.STEP_INCREMENT
                elif ragent.current_node_id in blue_territory:
                    # Blue team gets a point
                    blue_team_score += 1
                    # Reset only the red agent to its starting position
                    ragent.current_node_id = red_start_dict[red_agent]
                    ragent.prev_node_id = red_start_dict[red_agent]
                    max_steps += config.STEP_INCREMENT
                else:
                    # Reset the agents to their starting positions
                    ragent.current_node_id = red_start_dict[red_agent]
                    bagent.current_node_id = blue_start_dict[blue_agent]
                    ragent.prev_node_id = red_start_dict[red_agent]
                    bagent.prev_node_id = blue_start_dict[blue_agent]


def capture_rule(ctx):
    global max_steps
    global red_team_score
    global blue_team_score
    for red_agent in red_team:
        agent = ctx.agent.get_agent(red_agent)
        for val in blue_start_dict.values():
            if agent.current_node_id == val:
                # Red team gets a point
                red_team_score += 1
                # Reset the agent to its starting position
                agent.current_node_id = red_start_dict[red_agent]
                agent.prev_node_id = red_start_dict[red_agent]
                max_steps += config.STEP_INCREMENT
    
    for blue_agent in blue_team:
        agent = ctx.agent.get_agent(blue_agent)
        for val in red_start_dict.values():
            if agent.current_node_id == val:
                # Blue team gets a point
                blue_team_score += 1
                # Reset the agent to its starting position
                agent.current_node_id = blue_start_dict[blue_agent]
                agent.prev_node_id = blue_start_dict[blue_agent]
                max_steps += config.STEP_INCREAMENT


def termination_rule(ctx):
    if step_counter >= max_steps or step_counter >= config.MAX_SIM_STEPS:
        ctx.terminate()


step_counter = 0 # initialize the step counter to 0
while not ctx.is_terminated(): # run the loop until the context is terminated
    step_counter += 1 # increment the step counter by 1
    for agent in ctx.agent.create_iter():
        # Get the current state of the agent
        state = agent.get_state() # get the state of the agent
        # Get human input to move the agent
        node = ctx.visual.human_input(agent.name, state)
        state['action'] = node
        agent.set_state() # set the state of the agent
    

    ctx.visual.simulate() # Draw loop for the visual engine
    capture_rule(ctx) # check capture rule
    tag_rule(ctx) # check tag rule
    termination_rule(ctx) # check termination rule
