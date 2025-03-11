from gamms.VisualizationEngine import Color
from gamms.VisualizationEngine.builtin_artists import AgentData, GraphData
from gamms.context import Context

import math


def render_agent(ctx: Context, data: dict):
    """
    Render an agent as a triangle at its current position on the screen. This is the default rendering method for agents.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data dictionary.
    """
    agent_data: AgentData = data['agent_data']
    size = agent_data.size
    color = agent_data.color
    if agent_data.name == ctx.visual._waiting_agent_name:
        color = Color.Magenta
        size = agent_data.size * 1.5

    agent = ctx.agent.get_agent(agent_data.name)
    target_node = ctx.graph.graph.get_node(agent.current_node_id)
    if ctx.visual._waiting_simulation:
        prev_node = ctx.graph.graph.get_node(agent.prev_node_id)
        prev_position = (prev_node.x, prev_node.y)
        target_position = (target_node.x, target_node.y)
        edges = ctx.graph.graph.get_edges()
        current_edge = None
        for _, edge in edges.items():
            if edge.source == agent.prev_node_id and edge.target == agent.current_node_id:
                current_edge = edge

        alpha = ctx.visual._simulation_time / ctx.visual._sim_time_constant
        alpha = min(1, max(0, alpha))
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


def render_graph(ctx: Context, data: dict):
    """
    Render the graph by drawing its nodes and edges on the screen. This is the default rendering method for graphs.

    Args:
        ctx (Context): The current simulation context.
        data (dict): The data dictionary.
    """
    graph_data: GraphData = data['graph_data']
    graph = ctx.graph.graph
    node_color = graph_data.node_color
    edge_color = graph_data.edge_color
    draw_id = graph_data.draw_id
    target_node_id_set = None
    if ctx.visual._waiting_agent_name:
        target_node_id_set = set(ctx.visual._input_options.values())

    for edge in graph.get_edges().values():
        _render_graph_edge(ctx, graph_data, graph, edge, edge_color, target_node_id_set)
    for node in graph.get_nodes().values():
        _render_graph_node(ctx, node, node_color, draw_id)


def _render_graph_edge(ctx, graph_data, graph, edge, edge_color, target_node_id_set):
    """Draw an edge as a curve or straight line based on the linestring."""
    source = graph.get_node(edge.source)
    target = graph.get_node(edge.target)

    if ctx.visual._render_manager.check_line_culled(source.x, source.y, target.x, target.y):
        return

    color = edge_color
    if ctx.visual._waiting_agent_name:
        current_waiting_agent = ctx.agent.get_agent(ctx.visual._waiting_agent_name)
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
        ctx.visual.render_lines(line_points, color, is_aa=True, perform_culling_test=False)
    else:
        ctx.visual.render_line(source.x, source.y, target.x, target.y, color, 2, perform_culling_test=False)


def _render_graph_node(ctx, node, node_color=(169, 169, 169), draw_id=False):
    if ctx.visual._render_manager.check_circle_culled(node.x, node.y, 10):
        return

    if ctx.visual._waiting_user_input and node.id in ctx.visual._input_options.values():
        color = (0, 255, 0)
        radius = 8
    else:
        color = node_color
        radius = 4

    ctx.visual.render_circle(node.x, node.y, radius, color)

    if draw_id:
        ctx.visual.render_text(str(node.id), node.x, node.y + 10, (0, 0, 0))