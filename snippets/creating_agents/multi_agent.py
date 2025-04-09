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
    if step_counter == config.SIM_STEPS:
        ctx.terminate() # terminate the context after 20 steps
