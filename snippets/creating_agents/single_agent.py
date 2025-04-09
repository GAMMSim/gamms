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

# Create an agent
ctx.agent.create_agent(name='agent_0', start_node_id=0)

# Create a neighbor sensor
ctx.sensor.create_sensor(sensor_id='neigh_0', sensor_type=gamms.sensor.SensorType.NEIGHBOR)

# Register the sensor to the agent
ctx.agent.get_agent('agent_0').register_sensor(name='neigh_0', sensor=ctx.sensor.get_sensor('neigh_0'))

# Create the agent visualization
# set the agent visualization with name 'agent_0', color red and size 10
ctx.visual.set_agent_visual(name='agent_0', color=(255, 0, 0), size=10)

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
    if step_counter == 20:
        ctx.terminate() # terminate the context after 20 steps
