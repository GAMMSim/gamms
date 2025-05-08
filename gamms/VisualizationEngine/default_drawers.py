from gamms.VisualizationEngine import Color
from gamms.VisualizationEngine.builtin_artists import AgentData, GraphData
from gamms.typing import IContext, OSMEdge, Node, ColorType

from typing import Dict, Any, cast, List

import math


def render_circle(ctx: IContext, data: Dict[str, Any]):
    """
    Render a circle at the specified position with the specified radius and color.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data containing the circle's position, radius, and color.
    """
    x = data.get('x')
    y = data.get('y')
    radius = data.get('radius')
    color = data.get('color', Color.Cyan)
    ctx.visual.render_circle(x, y, radius, color)


def render_rectangle(ctx: IContext, data: Dict[str, Any]):
    """
    Render a rectangle at the specified position with the specified width, height, and color.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data containing the rectangle's position, width, height, and color.
    """
    x = data.get('x')
    y = data.get('y')
    width = data.get('width')
    height = data.get('height')
    color = data.get('color', Color.Cyan)
    ctx.visual.render_rectangle(x, y, width, height, color)

def render_agent(ctx: IContext, data: Dict[str, Any]):
    """
    Render an agent as a triangle at its current position on the screen. This is the default rendering method for agents.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data containing the agent's information.
    """
    agent_data = cast(AgentData, data.get('agent_data'))
    size = agent_data.size
    color = agent_data.color
    is_waiting = data.get('_is_waiting', False)
    if is_waiting:
        color = Color.Magenta
        size = agent_data.size * 1.5

    agent = ctx.agent.get_agent(agent_data.name)
    target_node = ctx.graph.graph.get_node(agent.current_node_id)
    waiting_simulation = data.get('_waiting_simulation', False)
    if waiting_simulation:
        prev_node = ctx.graph.graph.get_node(agent.prev_node_id)
        prev_position = (prev_node.x, prev_node.y)
        target_position = (target_node.x, target_node.y)
        current_edge = None
        for edge_id in ctx.graph.graph.get_edges():
            edge = ctx.graph.graph.get_edge(edge_id)
            if edge.source == agent.prev_node_id and edge.target == agent.current_node_id:
                current_edge = edge

        alpha = cast(float, data.get('_alpha'))
        if current_edge is not None:
            point = current_edge.linestring.interpolate(alpha, True)
            position = (point.x, point.y)
        else:
            position = (prev_position[0] + alpha * (target_position[0] - prev_position[0]), 
                        prev_position[1] + alpha * (target_position[1] - prev_position[1]))
            
        agent_data.current_position = position
    else:
        position = (target_node.x, target_node.y)

    # Draw each agent as a triangle at its current position
    angle = math.radians(45)
    point1 = (position[0] + size * math.cos(angle), position[1] + size * math.sin(angle))
    point2 = (position[0] + size * math.cos(angle + 2.5), position[1] + size * math.sin(angle + 2.5))
    point3 = (position[0] + size * math.cos(angle - 2.5), position[1] + size * math.sin(angle - 2.5))

    ctx.visual.render_polygon([point1, point2, point3], color)


def render_graph(ctx: IContext, data: Dict[str, Any]):
    """
    Render the graph by drawing its nodes and edges on the screen. This is the default rendering method for graphs.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data containing the graph's information.
    """
    graph_data = cast(GraphData, data.get('graph_data'))
    node_color = graph_data.node_color
    node_size = graph_data.node_size
    edge_color = graph_data.edge_color
    draw_id = graph_data.draw_id

    for edge_id in ctx.graph.graph.get_edges():
        edge = ctx.graph.graph.get_edge(edge_id)
        _render_graph_edge(ctx, graph_data, edge, edge_color)
        
    for node_id in ctx.graph.graph.get_nodes():
        node = ctx.graph.graph.get_node(node_id)
        _render_graph_node(ctx, node, node_color, node_size, draw_id)

def render_input_overlay(ctx: IContext, data: Dict[str, Any]):
    """
    Render the graph by drawing its nodes and edges on the screen. This is the default rendering method for graphs.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data containing the graph's information.
    """
    graph_data = cast(GraphData, data.get('graph_data'))
    waiting_agent_name = data.get('_waiting_agent_name', None)
    input_options = data.get('_input_options', {})
    waiting_user_input = data.get('_waiting_user_input', False)

    # Break checker
    if waiting_agent_name == None or waiting_user_input == False or input_options == {}:
        return
    
    graph = ctx.graph.graph
    node_color = graph_data.node_color
    node_size = graph_data.node_size
    edge_color = graph_data.edge_color
    draw_id = graph_data.draw_id
    target_node_id_set = set(input_options.values())

    for node in target_node_id_set:
        _render_graph_node(ctx, graph.get_node(node), node_color, node_size, draw_id)

    active_edges: List[OSMEdge] = []
    for edge_id in graph.get_edges():
        edge = graph.get_edge(edge_id)
        current_waiting_agent = ctx.agent.get_agent(waiting_agent_name)
        if (edge.source == current_waiting_agent.current_node_id and edge.target in target_node_id_set):
            active_edges.append(edge)

    for edge in active_edges:
        _render_graph_edge(ctx, graph_data, edge, edge_color)

def _render_graph_edge(ctx: IContext, graph_data: GraphData, edge: OSMEdge, color: ColorType):
    """Draw an edge as a curve or straight line based on the linestring."""
    source = ctx.graph.graph.get_node(edge.source)
    target = ctx.graph.graph.get_node(edge.target)

    if edge.linestring:
        edge_line_points = graph_data.edge_line_points
        if edge.id not in edge_line_points:
            # linestring[1:-1]
            linestring = ([(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] +
                            [(target.x, target.y)])
            edge_line_points[edge.id] = linestring

        line_points = edge_line_points[edge.id]
        ctx.visual.render_linestring(line_points, color, is_aa=True, perform_culling_test=False)
    else:
        ctx.visual.render_line(source.x, source.y, target.x, target.y, color, 2, perform_culling_test=False, is_aa=False)


def _render_graph_node(ctx: IContext, node: Node, color: ColorType, radius: float, draw_id: bool):
    ctx.visual.render_circle(node.x, node.y, radius, color)

    if draw_id:
        ctx.visual.render_text(str(node.id), node.x, node.y + 10, (0, 0, 0))


def render_neighbor_sensor(ctx: IContext, data: Dict[str, Any]):
    """
    Render a neighbor sensor.

    Args:
        ctx (Context): The current simulation context.
        data (Dict[str, Any]): The data containing the sensor's information.
    """
    sensor = ctx.sensor.get_sensor(data.get('name'))
    color = data.get('color', Color.Cyan)
    sensor_data = cast(List[int], sensor.data)
    for neighbor_node_id in sensor_data:
        neighbor_node = ctx.graph.graph.get_node(neighbor_node_id)
        ctx.visual.render_circle(neighbor_node.x, neighbor_node.y, 2, color)


def render_map_sensor(ctx: IContext, data: Dict[str, Any]):
    """
    Render a map sensor.

    Args:
        ctx (Context): The current simulation context.
        data (Dict[str, Any]): The data containing the sensor's information.
    """
    sensor = ctx.sensor.get_sensor(data.get('name'))
    node_color = data.get('node_color', Color.Cyan)
    sensor_data = cast(Dict[str, Any], sensor.data)

    sensed_nodes = cast(Dict[int, Node], sensor_data.get('nodes', {}))
    sensed_nodes = list(sensed_nodes.keys())
    for node_id in sensed_nodes:
        node = ctx.graph.graph.get_node(node_id)
        ctx.visual.render_circle(node.x, node.y, 1, node_color)

    edge_color = data.get('edge_color', Color.Cyan)
    sensed_edges = sensor_data.get('edges', [])
    
    for edge in sensed_edges:
        source = ctx.graph.graph.get_node(edge.source)
        target = ctx.graph.graph.get_node(edge.target)

        if edge.linestring:
            # linestring[1:-1]
            line_points = ([(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] +
                            [(target.x, target.y)])

            ctx.visual.render_linestring(line_points, edge_color, 4, is_aa=False, perform_culling_test=False)
        else:
            ctx.visual.render_line(source.x, source.y, target.x, target.y, edge_color, 4, perform_culling_test=False)


def render_agent_sensor(ctx: IContext, data: Dict[str, Any]):
    """
    Render an agent sensor.

    Args:
        ctx (Context): The current simulation context.
        data (Dict[str, Any]): The data containing the sensor's information.
    """
    sensor = ctx.sensor.get_sensor(data.get('name'))
    color = data.get('color', Color.Cyan)
    size = data.get('size', 8)
    sensor_data = cast(Dict[str, int], sensor.data)
    for node_id in sensor_data.values():
        target_node = ctx.graph.graph.get_node(node_id)
        position = (target_node.x, target_node.y)

        angle = math.radians(45)
        point1 = (position[0] + size * math.cos(angle), position[1] + size * math.sin(angle))
        point2 = (position[0] + size * math.cos(angle + 2.5), position[1] + size * math.sin(angle + 2.5))
        point3 = (position[0] + size * math.cos(angle - 2.5), position[1] + size * math.sin(angle - 2.5))

        ctx.visual.render_polygon([point1, point2, point3], color)