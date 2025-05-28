#!/usr/bin/env python3
import gamms
import pickle
import math
import numpy as np
from gamms.typing.sensor_engine import SensorType
from gamms.SensorEngine.sensor_engine import SensorEngine

def test_memory_engine():
    """Test basic memory engine functionality"""
    print("=" * 60)
    print("TESTING MEMORY ENGINE")
    print("=" * 60)
    
    ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)
    
    # Test connection
    conn_status = ctx.memory.check_connection()
    print(f"✓ Database connection: {'OK' if conn_status else 'FAILED'}")
    assert conn_status, "Database connection failed"
    
    # Test store creation
    test_store = ctx.memory.create_store(
        name="test_table",
        schema={"id": "INTEGER", "name": "TEXT", "value": "REAL"},
        primary_key="id"
    )
    print("✓ Store creation: OK")
    
    # Test store operations
    test_store.save({"id": 1, "name": "test1", "value": 3.14})
    test_store.save({"id": 2, "name": "test2", "value": 2.71})
    
    loaded = test_store.load(1)
    assert loaded["name"] == "test1" and loaded["value"] == 3.14
    print("✓ Store save/load: OK")
    
    # Test queries
    results = test_store.query("SELECT * FROM test_table WHERE value > ?", [3.0])
    assert len(results) == 1 and results[0]["name"] == "test1"
    print("✓ Store queries: OK")
    
    ctx.terminate()
    print("✓ Memory engine tests: PASSED\n")

def test_graph_engine():
    """Test graph engine functionality"""
    print("=" * 60)
    print("TESTING GRAPH ENGINE")
    print("=" * 60)
    
    ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)
    
    # Test loading graph from pickle
    try:
        with open("graph.pkl", 'rb') as f:
            G_nx = pickle.load(f)
        print(f"✓ Loaded NetworkX graph with {len(G_nx.nodes)} nodes and {len(G_nx.edges)} edges")
    except FileNotFoundError:
        print("! No graph.pkl found, creating test graph")
        import networkx as nx
        G_nx = nx.grid_2d_graph(5, 5)  # 5x5 grid
        # Add coordinates and convert to integers
        G_nx = nx.convert_node_labels_to_integers(G_nx)
        for i, (u, v) in enumerate(G_nx.edges()):
            G_nx.edges[u, v]['id'] = i
            G_nx.edges[u, v]['length'] = 1.0
        
        pos = nx.spring_layout(G_nx, seed=42)
        for node in G_nx.nodes():
            G_nx.nodes[node]['x'] = pos[node][0] * 100
            G_nx.nodes[node]['y'] = pos[node][1] * 100
    
    # Attach graph to engine
    graph = ctx.graph.attach_networkx_graph(G_nx)
    print("✓ Graph attached to engine")
    
    # Verify nodes and edges were stored
    nodes = graph.get_nodes()
    edges = graph.get_edges()
    print(f"✓ Stored {len(nodes)} nodes and {len(edges)} edges")
    
    # Test individual node/edge operations
    if len(nodes) > 0:
        test_node = nodes[0]
        retrieved_node = graph.get_node(test_node.id)
        assert retrieved_node.id == test_node.id
        print("✓ Node retrieval: OK")
    
    if len(edges) > 0:
        test_edge = edges[0]
        retrieved_edge = graph.get_edge(test_edge.id)
        assert retrieved_edge.id == test_edge.id
        print("✓ Edge retrieval: OK")
    
    # Test adding new nodes and edges
    new_node_id = max([n.id for n in nodes]) + 1 if nodes else 1000
    graph.add_node({"id": new_node_id, "x": 999.0, "y": 888.0})
    new_node = graph.get_node(new_node_id)
    assert new_node.x == 999.0 and new_node.y == 888.0
    print("✓ New node addition: OK")
    
    new_edge_id = max([e.id for e in edges]) + 1 if edges else 1000
    if len(nodes) >= 2:
        graph.add_edge({
            "id": new_edge_id, 
            "source": nodes[0].id, 
            "target": nodes[1].id, 
            "length": 123.4
        })
        new_edge = graph.get_edge(new_edge_id)
        assert new_edge.length == 123.4
        print("✓ New edge addition: OK")
    
    # Test node/edge updates
    graph.update_node({"id": new_node_id, "x": 777.0})
    updated_node = graph.get_node(new_node_id)
    assert updated_node.x == 777.0 and updated_node.y == 888.0  # y should be preserved
    print("✓ Node update: OK")
    
    ctx.terminate()
    print("✓ Graph engine tests: PASSED\n")
    return G_nx  # Return for use in agent tests

def test_agent_engine(G_nx):
    """Test agent engine functionality"""
    print("=" * 60)
    print("TESTING AGENT ENGINE")
    print("=" * 60)
    
    ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)
    ctx.graph.attach_networkx_graph(G_nx)
    
    nodes = ctx.graph.graph.get_nodes()
    if len(nodes) < 5:
        print("! Not enough nodes for comprehensive agent testing")
        ctx.terminate()
        return ctx
    
    # Test agent creation
    agent1 = ctx.agent.create_agent(
        "test_agent_1",
        start_node_id=nodes[0].id,
        team=1,
        color="red"
    )
    print("✓ Agent creation: OK")
    
    # Test agent properties
    assert agent1.name == "test_agent_1"
    assert agent1.current_node_id == nodes[0].id
    assert agent1.prev_node_id == nodes[0].id
    print("✓ Agent properties: OK")
    
    # Test agent movement and orientation
    agent1.current_node_id = nodes[1].id
    agent1.prev_node_id = nodes[0].id
    
    orientation = agent1.orientation
    assert len(orientation) == 2  # Should be (cos, sin) tuple
    print(f"✓ Agent orientation: {orientation}")
    
    # Test multiple agents
    for i in range(2, min(6, len(nodes))):
        ctx.agent.create_agent(
            f"test_agent_{i}",
            start_node_id=nodes[i].id,
            team=i % 2
        )
    
    agents = list(ctx.agent.create_iter())
    print(f"✓ Created {len(agents)} agents")
    
    # Test agent retrieval
    retrieved_agent = ctx.agent.get_agent("test_agent_1")
    assert retrieved_agent.name == "test_agent_1"
    print("✓ Agent retrieval: OK")
    
    # Test agent deletion
    ctx.agent.delete_agent("test_agent_5")
    try:
        ctx.agent.get_agent("test_agent_5")
        assert False, "Should have raised KeyError"
    except KeyError:
        print("✓ Agent deletion: OK")
    
    print("✓ Agent engine tests: PASSED\n")
    return ctx

def test_sensors_comprehensive(ctx):
    """Comprehensive sensor testing"""
    print("=" * 60)
    print("TESTING SENSORS COMPREHENSIVELY")
    print("=" * 60)
    
    nodes = ctx.graph.graph.get_nodes()
    agents = list(ctx.agent.create_iter())
    
    if len(nodes) < 3 or len(agents) < 3:
        print("! Insufficient nodes/agents for comprehensive sensor testing")
        return
    
    sensor_engine = SensorEngine(ctx)
    
    # Test 1: NEIGHBOR Sensor
    print("\n--- Testing NEIGHBOR Sensor ---")
    neighbor_sensor = sensor_engine.create_sensor("neighbor_test", SensorType.NEIGHBOR)
    
    for i, node in enumerate(nodes[:3]):
        neighbor_sensor.sense(node.id)
        neighbors = neighbor_sensor.data
        print(f"Node {node.id} neighbors: {neighbors}")
        assert isinstance(neighbors, list), "Neighbor data should be a list"
    
    print("✓ NEIGHBOR sensor: OK")
    
    # Test 2: MAP Sensor (should see all nodes)
    print("\n--- Testing MAP Sensor ---")
    map_sensor = sensor_engine.create_sensor("map_test", SensorType.MAP)
    map_sensor.sense(nodes[0].id)
    
    map_data = map_sensor.data
    assert 'nodes' in map_data and 'edges' in map_data
    print(f"MAP sensor detected {len(map_data['nodes'])} nodes and {len(map_data['edges'])} edges")
    assert len(map_data['nodes']) == len(nodes), "MAP sensor should detect all nodes"
    print("✓ MAP sensor: OK")
    
    # Test 3: RANGE Sensor
    print("\n--- Testing RANGE Sensor ---")
    range_sensor = sensor_engine.create_sensor("range_test", SensorType.RANGE, sensor_range=50.0)
    range_sensor.sense(nodes[0].id)
    
    range_data = range_sensor.data
    print(f"RANGE sensor detected {len(range_data['nodes'])} nodes within range 50")
    assert len(range_data['nodes']) <= len(nodes), "RANGE sensor should detect subset of nodes"
    print("✓ RANGE sensor: OK")
    
    # Test 4: ARC Sensor with owner
    print("\n--- Testing ARC Sensor ---")
    arc_sensor = sensor_engine.create_sensor(
        "arc_test", 
        SensorType.ARC, 
        sensor_range=100.0, 
        fov=math.radians(90)
    )
    arc_sensor.set_owner(agents[0].name)
    
    # Move agent to create meaningful orientation
    agents[0].prev_node_id = nodes[0].id
    agents[0].current_node_id = nodes[1].id
    
    arc_sensor.sense(nodes[0].id)
    arc_data = arc_sensor.data
    print(f"ARC sensor detected {len(arc_data['nodes'])} nodes in 90° arc")
    print("✓ ARC sensor: OK")
    
    # Test 5: AGENT Sensor
    print("\n--- Testing AGENT Sensor ---")
    agent_sensor = sensor_engine.create_sensor("agent_test", SensorType.AGENT)
    agent_sensor.set_owner(agents[0].name)
    agent_sensor.sense(agents[0].current_node_id)
    
    agent_data = agent_sensor.data
    print(f"AGENT sensor detected agents: {list(agent_data.keys())}")
    assert agents[0].name not in agent_data, "Agent sensor should not detect owner"
    print("✓ AGENT sensor: OK")
    
    # Test 6: AGENT_RANGE Sensor
    print("\n--- Testing AGENT_RANGE Sensor ---")
    agent_range_sensor = sensor_engine.create_sensor(
        "agent_range_test", 
        SensorType.AGENT_RANGE, 
        sensor_range=100.0
    )
    agent_range_sensor.set_owner(agents[0].name)
    agent_range_sensor.sense(agents[0].current_node_id)
    
    agent_range_data = agent_range_sensor.data
    print(f"AGENT_RANGE sensor detected agents: {list(agent_range_data.keys())}")
    print("✓ AGENT_RANGE sensor: OK")
    
    # Test 7: AGENT_ARC Sensor
    print("\n--- Testing AGENT_ARC Sensor ---")
    agent_arc_sensor = sensor_engine.create_sensor(
        "agent_arc_test", 
        SensorType.AGENT_ARC, 
        sensor_range=100.0,
        fov=math.radians(120)
    )
    agent_arc_sensor.set_owner(agents[0].name)
    agent_arc_sensor.sense(agents[0].current_node_id)
    
    agent_arc_data = agent_arc_sensor.data
    print(f"AGENT_ARC sensor detected agents: {list(agent_arc_data.keys())}")
    print("✓ AGENT_ARC sensor: OK")
    
    print("✓ All sensor tests: PASSED\n")

def test_sensor_edge_cases(ctx):
    """Test sensor edge cases and error conditions"""
    print("=" * 60)
    print("TESTING SENSOR EDGE CASES")
    print("=" * 60)
    
    sensor_engine = SensorEngine(ctx)
    nodes = ctx.graph.graph.get_nodes()
    
    if not nodes:
        print("! No nodes available for edge case testing")
        return
    
    # Test sensing from non-existent node
    print("\n--- Testing non-existent node ---")
    neighbor_sensor = sensor_engine.create_sensor("edge_test", SensorType.NEIGHBOR)
    neighbor_sensor.sense(99999)  # Non-existent node
    print(f"Sensing non-existent node result: {neighbor_sensor.data}")
    
    # Test zero range sensor
    print("\n--- Testing zero range sensor ---")
    zero_range_sensor = sensor_engine.create_sensor(
        "zero_range_test", 
        SensorType.RANGE, 
        sensor_range=0.0
    )
    zero_range_sensor.sense(nodes[0].id)
    zero_data = zero_range_sensor.data
    print(f"Zero range sensor detected {len(zero_data['nodes'])} nodes")
    
    # Test very large range sensor
    print("\n--- Testing very large range sensor ---")
    large_range_sensor = sensor_engine.create_sensor(
        "large_range_test", 
        SensorType.RANGE, 
        sensor_range=1000000.0
    )
    large_range_sensor.sense(nodes[0].id)
    large_data = large_range_sensor.data
    print(f"Large range sensor detected {len(large_data['nodes'])} nodes")
    
    # Test very narrow FOV
    print("\n--- Testing very narrow FOV ---")
    narrow_fov_sensor = sensor_engine.create_sensor(
        "narrow_fov_test", 
        SensorType.ARC, 
        sensor_range=100.0,
        fov=math.radians(1)  # 1 degree
    )
    narrow_fov_sensor.sense(nodes[0].id)
    narrow_data = narrow_fov_sensor.data
    print(f"Narrow FOV sensor detected {len(narrow_data['nodes'])} nodes")
    
    print("✓ Edge case tests: PASSED\n")

def test_performance_basic(ctx):
    """Basic performance test with multiple operations"""
    print("=" * 60)
    print("TESTING BASIC PERFORMANCE")
    print("=" * 60)
    
    import time
    
    nodes = ctx.graph.graph.get_nodes()
    agents = list(ctx.agent.create_iter())
    sensor_engine = SensorEngine(ctx)
    
    if len(nodes) < 10:
        print("! Not enough nodes for performance testing")
        return
    
    # Create various sensors
    sensors = [
        sensor_engine.create_sensor("perf_neighbor", SensorType.NEIGHBOR),
        sensor_engine.create_sensor("perf_range", SensorType.RANGE, sensor_range=50.0),
        sensor_engine.create_sensor("perf_agent", SensorType.AGENT),
    ]
    
    # Time multiple sensing operations
    start_time = time.time()
    iterations = 50
    
    for i in range(iterations):
        test_node = nodes[i % len(nodes)]
        for sensor in sensors:
            sensor.sense(test_node.id)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"✓ Performed {iterations * len(sensors)} sensor operations in {total_time:.3f}s")
    print(f"✓ Average time per operation: {(total_time / (iterations * len(sensors)) * 1000):.2f}ms")
    
    print("✓ Performance test: PASSED\n")

def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 STARTING COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    try:
        # Test 1: Memory Engine
        test_memory_engine()
        
        # Test 2: Graph Engine
        G_nx = test_graph_engine()
        
        # Test 3: Agent Engine
        ctx = test_agent_engine(G_nx)
        
        # Test 4: Comprehensive Sensor Tests
        test_sensors_comprehensive(ctx)
        
        # Test 5: Edge Cases
        test_sensor_edge_cases(ctx)
        
        # Test 6: Basic Performance
        test_performance_basic(ctx)
        
        # Cleanup
        ctx.terminate()
        
        print("=" * 80)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_all_tests()