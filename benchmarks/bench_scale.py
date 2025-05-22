import gamms
import random

from typing import Callable

def create_grid(graph, n):
    edge_count = 0 # initialize the edge count to 0
    for i in range(n):
        for j in range(n):
            # add a node to the graph with id i * n + j and coordinates (i, j)
            graph.add_node({'id': i * n + j, 'x': i * 100.0, 'y': j * 100.0})
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


def create_test(
    n: int = 10,
    n_agents: int = 10,
    map_sensors: bool = False,
) -> Callable[[], None]:
    sensor_config = {}
    for i in range(n_agents):
        sensor_config[f"neigh_{i}"] = {
            "type": gamms.sensor.SensorType.NEIGHBOR,
        }
        if map_sensors:
            sensor_config[f"map_{i}"] = {
                "type": gamms.sensor.SensorType.MAP,
                "sensor_range": 200,
            }
    
    agent_config = {}
    for i in range(n_agents):
        agent_config[f"agent_{i}"] = {'start_node_id': i}
        if map_sensors:
            agent_config[f"agent_{i}"]['sensors'] = [f"map_{i}", f"neigh_{i}"]
        else:
            agent_config[f"agent_{i}"]['sensors'] = [f"neigh_{i}"]
    
    ctx = gamms.create_context(logger_config={'level':'ERROR'})
    create_grid(ctx.graph.graph, n)

    def loop():
        for _ in range(200):
            states = {}
            for agent in ctx.agent.create_iter():
                states[agent.name] = agent.get_state()
            for agent in ctx.agent.create_iter():
                state = states[agent.name]
                state['action'] = random.choice(state['sensors'][f"neigh_{agent.name.split('_')[1]}"])
            
            for agent in ctx.agent.create_iter():
                agent.set_state()
            
            ctx.visual.simulate()
        
        ctx.terminate()
    
    return loop


__benchmarks__ = [
    (
        create_test(n=10, n_agents=10, map_sensors=False),
        create_test(n=10, n_agents=10, map_sensors=True),
        "10x10 grid 10 agents wo vs. w map sensors",
    ),
    (
        create_test(n=100, n_agents=10, map_sensors=False),
        create_test(n=1000, n_agents=10, map_sensors=False),
        "100x100 grid vs 1000x1000 grid",
    ),
    (
        create_test(n=100, n_agents=10, map_sensors=False),
        create_test(n=100, n_agents=100, map_sensors=False),
        "10 agents vs 100 agents",
    ),
    (
        create_test(n=100, n_agents=10, map_sensors=True),
        create_test(n=1000, n_agents=10, map_sensors=True),
        "100x100 grid vs 1000x1000 grid with map sensors",
    ),
]