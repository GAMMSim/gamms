import time
import gamms

# create a context with PYGAME as the visual engine
ctx = gamms.create_context(vis_engine=gamms.visual.Engine.PYGAME)

graph = ctx.graph.graph # get the graph object from the context

# Create a 1x1 grid

graph.add_node({'id': 0, 'x': 0, 'y': 0}) # add a node to the graph with id 0 and coordinates (0, 0)
graph.add_node({'id': 1, 'x': 100.0, 'y': 0}) # add a node to the graph with id 1 and coordinates (100, 0)
graph.add_node({'id': 2, 'x': 100.0, 'y': 100.0}) # add a node to the graph with id 2 and coordinates (100, 100)
graph.add_node({'id': 3, 'x': 0, 'y': 100.0}) # add a node to the graph with id 3 and coordinates (0, 100)
graph.add_edge({'id': 0, 'source': 0, 'target': 1, 'length': 1.0}) # add an edge to the graph with id 0 from node 0 to node 1
graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1.0}) # add an edge to the graph with id 1 from node 1 to node 2
graph.add_edge({'id': 2, 'source': 2, 'target': 3, 'length': 1.0}) # add an edge to the graph with id 2 from node 2 to node 3
graph.add_edge({'id': 3, 'source': 3, 'target': 0, 'length': 1.0}) # add an edge to the graph with id 3 from node 3 to node 0
graph.add_edge({'id': 4, 'source': 0, 'target': 3, 'length': 1.0}) # add an edge to the graph with id 4 from node 0 to node 3
graph.add_edge({'id': 5, 'source': 3, 'target': 2, 'length': 1.0}) # add an edge to the graph with id 5 from node 3 to node 2
graph.add_edge({'id': 6, 'source': 2, 'target': 1, 'length': 1.0}) # add an edge to the graph with id 6 from node 2 to node 1
graph.add_edge({'id': 7, 'source': 1, 'target': 0, 'length': 1.0}) # add an edge to the graph with id 7 from node 1 to node 0


# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(width=1980, height=1080) # set the graph visualization with width 1980 and height 1080

t = time.time() # get the current time
while time.time() - t < 120: # run the loop for 120 seconds
    ctx.visual.simulate() # Draw loop for the visual engine

ctx.terminate() # terminate the context