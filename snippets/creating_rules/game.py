import gamms
import config

ctx = gamms.create_context(vis_engine=config.VIS_ENGINE) # create a context with PYGAME as the visual engine

graph = ctx.graph.graph # get the graph object from the context

def create_grid(graph, n):
    edge_count = 0 # initialize the edge count to 0
    for i in range(n):
        for j in range(n):
            graph.add_node({'id': i * n + j, 'x': i * 100.0, 'y': j * 100.0}) # add a node to the graph with id i * n + j and coordinates (i, j)
            if i > 0:
                # add an edge to the graph from node (i - 1) * n + j to node i * n + j
                graph.add_edge({'id': edge_count, 'source': (i - 1) * n + j, 'target': i * n + j, 'length': 1.0})
                # add an edge to the graph from node i * n + j to node (i - 1) * n + j
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': (i - 1) * n + j, 'length': 1.0})
                edge_count += 2 # increment the edge count by 2
            if j > 0:
                # add an edge to the graph from node i * n + (j - 1) to node i * n + j
                graph.add_edge({'id': edge_count, 'source': i * n + (j - 1), 'target': i * n + j, 'length': 1.0})
                # add an edge to the graph from node i * n + j to node i * n + (j - 1)
                graph.add_edge({'id': edge_count + 1, 'source': i * n + j, 'target': i * n + (j - 1), 'length': 1.0})
                edge_count += 2 # increment the edge count by 2

create_grid(graph, config.GRID_SIZE)

# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(**config.graph_vis_config) # set the graph visualization with width 1980 and height 1080

# Create all the sensors
for name, sensor in config.sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor)

# Create all the agents
for name, agent in config.agent_config.items():
    ctx.agent.create_agent(name, **agent)


# Create all agents visualization
for name, vis_config in config.agent_vis_config.items():
    ctx.visual.set_agent_visual(name, **vis_config)


red_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 0]
blue_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 1]
red_start_dict = {name: config.agent_config[name]['start_node_id'] for name in red_team}
blue_start_dict = {name: config.agent_config[name]['start_node_id'] for name in blue_team}

def tag_rule(ctx):
    for red_agent in red_team:
        for blue_agent in blue_team:
            ragent = ctx.agent.get_agent(red_agent)
            bagent = ctx.agent.get_agent(blue_agent)
            if ragent.current_node_id == bagent.current_node_id:
                # Reset the agents to their starting positions
                ragent.current_node_id = red_start_dict[red_agent]
                bagent.current_node_id = blue_start_dict[blue_agent]
                ragent.prev_node_id = red_start_dict[red_agent]
                bagent.prev_node_id = blue_start_dict[blue_agent]



red_team_score = 0
blue_team_score = 0
max_steps = 120

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
                max_steps += 10
    
    for blue_agent in blue_team:
        agent = ctx.agent.get_agent(blue_agent)
        for val in red_start_dict.values():
            if agent.current_node_id == val:
                # Blue team gets a point
                blue_team_score += 1
                # Reset the agent to its starting position
                agent.current_node_id = blue_start_dict[blue_agent]
                agent.prev_node_id = blue_start_dict[blue_agent]
                max_steps += 10


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
