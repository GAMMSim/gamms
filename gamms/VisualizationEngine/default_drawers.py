from gamms.VisualizationEngine import Color
from gamms.VisualizationEngine.builtin_artists import AgentData, GraphData
from gamms.typing.artist import IArtist
from gamms.context import Context

import math


def render_circle(ctx: Context, artist: IArtist):
    """
    Render a circle at the specified position with the specified radius and color.

    Args:
        ctx (Context): The current simulation context.
        artist (IArtist): The artist object containing the circle data.
    """
    x = artist.get_data('x')
    y = artist.get_data('y')
    radius = artist.get_data('radius')
    color = artist.get_data('color', Color.Cyan)
    ctx.visual.render_circle(x, y, radius, color, artist.get_layer())


def render_rectangle(ctx: Context, artist: IArtist):
    """
    Render a rectangle at the specified position with the specified width, height, and color.

    Args:
        ctx (Context): The current simulation context.
        artist (IArtist): The artist object containing the rectangle data.
    """
    x = artist.get_data('x')
    y = artist.get_data('y')
    width = artist.get_data('width')
    height = artist.get_data('height')
    color = artist.get_data('color', Color.Cyan)
    ctx.visual.render_rectangle(x, y, width, height, color, artist.get_layer())

def render_agent(ctx: Context, artist: IArtist):
    """
    Render an agent as a triangle at its current position on the screen. This is the default rendering method for agents.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data dictionary.
    """
    agent_data: AgentData = artist.get_data('agent_data')
    size = agent_data.size
    color = agent_data.color
    is_waiting = artist.get_data('_is_waiting', False)
    if is_waiting:
        color = Color.Magenta
        size = agent_data.size * 1.5

    agent = ctx.agent.get_agent(agent_data.name)
    target_node = ctx.graph.graph.get_node(agent.current_node_id)
    if ctx.visual.is_waiting_simulation():
        prev_node = ctx.graph.graph.get_node(agent.prev_node_id)
        prev_position = (prev_node.x, prev_node.y)
        target_position = (target_node.x, target_node.y)
        edges = ctx.graph.graph.get_edges()
        current_edge = None
        for _, edge in edges.items():
            if edge.source == agent.prev_node_id and edge.target == agent.current_node_id:
                current_edge = edge

        alpha = artist.get_data('_alpha')
        if current_edge is not None:
            point = current_edge.linestring.interpolate(alpha, True)
            position = (point.x, point.y)
        else:
            position = (prev_position[0] + alpha * (target_position[0] - prev_position[0]), 
                        prev_position[1] + alpha * (target_position[1] - prev_position[1]))
            
        agent_data.current_position = position
    else:
        if agent_data.current_position is None:
            position = (target_node.x, target_node.y)
            agent_data.current_position = position
        else:
            position = agent_data.current_position

    # Draw each agent as a triangle at its current position
    angle = math.radians(45)
    point1 = (position[0] + size * math.cos(angle), position[1] + size * math.sin(angle))
    point2 = (position[0] + size * math.cos(angle + 2.5), position[1] + size * math.sin(angle + 2.5))
    point3 = (position[0] + size * math.cos(angle - 2.5), position[1] + size * math.sin(angle - 2.5))

    ctx.visual.render_polygon([point1, point2, point3], color)


def render_graph(ctx: Context, artist: IArtist):
    """
    Render the graph by drawing its nodes and edges on the screen. This is the default rendering method for graphs.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data dictionary.
    """
    graph_data: GraphData = artist.get_data('graph_data')
    layer = artist.get_layer()
    waiting_agent_name = artist.get_data('_waiting_agent_name')
    input_options = artist.get_data('_input_options', {})
    graph = ctx.graph.graph
    node_color = graph_data.node_color
    edge_color = graph_data.edge_color
    draw_id = graph_data.draw_id
    target_node_id_set = None
    if waiting_agent_name:
        target_node_id_set = set(input_options.values())

    # ctx.visual.fill_layer(layer, Color.Cyan)

    for edge in graph.get_edges().values():
        _render_graph_edge(ctx, graph_data, graph, edge, edge_color, layer, waiting_agent_name, target_node_id_set)
    for node in graph.get_nodes().values():
        _render_graph_node(ctx, node, node_color, draw_id, layer, input_options)


def _render_graph_edge(ctx: Context, graph_data, graph, edge, edge_color, layer, waiting_agent_name, target_node_id_set):
    """Draw an edge as a curve or straight line based on the linestring."""
    source = graph.get_node(edge.source)
    target = graph.get_node(edge.target)

    if ctx.visual._render_manager.check_line_culled(source.x, source.y, target.x, target.y):
        return

    color = edge_color
    if waiting_agent_name:
        current_waiting_agent = ctx.agent.get_agent(waiting_agent_name)
        if (current_waiting_agent is not None and edge.source == current_waiting_agent.current_node_id and
                edge.target in target_node_id_set):
            color = (0, 255, 0)

    if edge.linestring:
        edge_line_points = graph_data.edge_line_points
        if edge.id not in edge_line_points:
            # linestring[1:-1]
            source = graph.get_node(edge.source)
            target = graph.get_node(edge.target)
            linestring = ([(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] +
                            [(target.x, target.y)])
            edge_line_points[edge.id] = linestring

        line_points = edge_line_points[edge.id]
        ctx.visual.render_lines(line_points, color, layer=layer, is_aa=True, perform_culling_test=False)
    else:
        ctx.visual.render_line(source.x, source.y, target.x, target.y, color, 2, layer=layer, perform_culling_test=False)


def _render_graph_node(ctx: Context, node, node_color, draw_id, layer, input_options):
    if ctx.visual._render_manager.check_circle_culled(node.x, node.y, 10):
        return

    if ctx.visual.is_waiting_input() and node.id in input_options.values():
        color = (0, 255, 0)
        radius = 16
    else:
        color = node_color
        radius = 8

    ctx.visual.render_circle(node.x, node.y, radius, color, layer=layer)

    if draw_id:
        ctx.visual.render_text(str(node.id), node.x, node.y + 10, (0, 0, 0), layer=layer)


def render_neighbor_sensor(ctx: Context, artist: IArtist):
    """
    Render a neighbor sensor.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data dictionary.
    """
    sensor = artist.get_data('sensor')
    color = artist.get_data('color', Color.Cyan)
    sensor_data: dict = sensor.data
    for neighbor_node_id in sensor_data:
        neighbor_node = ctx.graph.graph.get_node(neighbor_node_id)
        ctx.visual.render_circle(neighbor_node.x, neighbor_node.y, 2, color)


def render_map_sensor(ctx: Context, artist: IArtist):
    """
    Render a map sensor.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data dictionary.
    """
    sensor = artist.get_data('sensor')
    node_color = artist.get_data('node_color', Color.Cyan)
    sensor_data: dict = sensor.data

    sensed_nodes = sensor_data.get('nodes', None)
    if sensed_nodes:
        sensed_nodes: list[int] = list(sensed_nodes.keys())
        for node_id in sensed_nodes:
            node = ctx.graph.graph.get_node(node_id)
            ctx.visual.render_circle(node.x, node.y, 2, node_color)

    edge_color = artist.get_data('edge_color', Color.Cyan)
    sensed_edges = sensor_data.get('edges', None)
    if sensed_edges:
        sensed_edges: list = list(  sensed_edges.values())
        for edge_list in sensed_edges:
            for edge in edge_list:
                source = ctx.graph.graph.get_node(edge.source)
                target = ctx.graph.graph.get_node(edge.target)

                if ctx.visual._render_manager.check_line_culled(source.x, source.y, target.x, target.y):
                    continue

                if edge.linestring:
                    # linestring[1:-1]
                    line_points = ([(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] +
                                    [(target.x, target.y)])

                    ctx.visual.render_lines(line_points, edge_color, is_aa=True, perform_culling_test=False)
                else:
                    ctx.visual.render_line(source.x, source.y, target.x, target.y, edge_color, 2, perform_culling_test=False)


def render_agent_sensor(ctx: Context, artist: IArtist):
    sensor = artist.get_data('sensor')
    color = artist.get_data('color', Color.Cyan)
    size = artist.get_data('size', 8)
    sensor_data: dict = sensor.data
    sensed_agents = list(sensor_data.values())
    for agent in sensed_agents:
        target_node = ctx.graph.graph.get_node(agent.current_node_id)
        position = (target_node.x, target_node.y)

        angle = math.radians(45)
        point1 = (position[0] + size * math.cos(angle), position[1] + size * math.sin(angle))
        point2 = (position[0] + size * math.cos(angle + 2.5), position[1] + size * math.sin(angle + 2.5))
        point3 = (position[0] + size * math.cos(angle - 2.5), position[1] + size * math.sin(angle - 2.5))

        ctx.visual.render_polygon([point1, point2, point3], color)