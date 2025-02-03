from gamms.VisualizationEngine import Color, Shape
from gamms.VisualizationEngine.render_node import RenderNode
from gamms.VisualizationEngine.agent_visual import AgentVisual
from gamms.typing.graph_engine import IGraph
from gamms.context import Context
import pygame
import math


class RenderManager:
    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self._render_nodes: dict[str, RenderNode] = {}

    def add_render_node(self, name: str, render_node: RenderNode):
        """
        Add a render node to the render manager. A render node can draw one or more shapes on the screen and may have a customized drawer.

        Args:
            name (str): The unique name of the render node.
            render_node (RenderNode): The render node to add to the render manager.
        """
        self._render_nodes[name] = render_node

    def remove_render_node(self, name: str):
        """
        Remove a render node from the render manager.

        Args:
            name (str): The unique name of the render node to remove.
        """
        if name in self._render_nodes:
            del self._render_nodes[name]
        else:
            print(f"Warning: Render node {name} not found.")

    def handle_render(self):
        """
        Render all render nodes in the render manager. This should be called every frame from the pygame engine to update the visualization.

        Raises:
            NotImplementedError: If the shape of a render node is not implemented and a custom drawer is not provided.
        """
        for render_node in self._render_nodes.values():
            # if use custom drawer
            if 'drawer' in render_node.data:
                drawer = render_node.drawer
                drawer(self.ctx, render_node.data)
                continue

            shape = render_node.shape
            if shape == Shape.Circle:
                RenderManager.render_circle(self.ctx, render_node.x, render_node.y, render_node.data['scale'], render_node.color)
            elif shape == Shape.Graph:
                RenderManager.render_graph(self.ctx, render_node.data['graph'])
            elif shape == Shape.Agent:
                RenderManager.render_agent(self.ctx, render_node.data['agent_visual'])
            else:
                raise NotImplementedError("Render node not implemented")

    @staticmethod
    def render_circle(ctx: Context, x: float, y: float, radius: float, color: tuple=Color.Black):
        """
        Render a circle at the given position with the given radius and color.

        Args:
            ctx (Context): The current simulation context.
            x (float): The x coordinate of the circle's center.
            y (float): The y coordinate of the circle's center.
            radius (float): The radius of the circle.
            color (tuple, optional): The color the the circle. Defaults to Color.Black.
        """
        (x, y) = ctx.visual._graph_visual.ScalePositionToScreen((x, y))
        
        _screen = ctx.visual.screen
        _width = _screen.get_width()
        _height = _screen.get_height()
        if (x < 0 or x > _width or y < 0 or y > _height):
            return

        pygame.draw.circle(ctx.visual.screen, color, (x, y), radius)

    @staticmethod
    def render_agent(ctx: Context, agent_visual: AgentVisual):
        """
        Render an agent as a triangle at its current position on the screen. This is the default rendering method for agents.

        Args:
            ctx (Context): The current simulation context.
            agent_visual (AgentVisual): The visual representation of the agent to render.
        """
        screen = ctx.visual.screen
        position = agent_visual.position
        size = agent_visual.size
        (scaled_x, scaled_y) = ctx.visual._graph_visual.ScalePositionToScreen(position)
        color = agent_visual.color
        if agent_visual.name == ctx.visual.waiting_agent_name:
            color = Color.Magenta

        # Draw each agent as a triangle at its current position
        angle = math.radians(45)
        point1 = (scaled_x + size * math.cos(angle), scaled_y + size * math.sin(angle))
        point2 = (scaled_x + size * math.cos(angle + 2.5), scaled_y + size * math.sin(angle + 2.5))
        point3 = (scaled_x + size * math.cos(angle - 2.5), scaled_y + size * math.sin(angle - 2.5))

        _width = screen.get_width()
        _height = screen.get_height()
        # Check points to cull
        if(point1[0] < 0 and point2[0] < 0 and point3[0] < 0) or (point1[0] > _width and point2[0] > _width and point3[0] > _width):
            return
        if(point1[1] < 0 and point2[1] < 0 and point3[1] < 0) or (point1[1] > _height and point2[1] > _height and point3[1] > _height):
            return

        pygame.draw.polygon(screen, color, [point1, point2, point3])

    @staticmethod
    def render_graph(ctx: Context, graph: IGraph):
        """
        Render the graph by drawing its nodes and edges on the screen. This is the default rendering method for graphs.

        Args:
            ctx (Context): The current simulation context.
            graph (IGraph): The graph to render.
        """
        screen = ctx.visual.screen
        for edge in graph.edges.values():
            RenderManager._draw_edge(ctx, screen, graph, edge)
        for node in graph.nodes.values():
            RenderManager._draw_node(ctx, screen, node)

    @staticmethod
    def _draw_edge(ctx, screen, graph, edge):
        """Draw an edge as a curve or straight line based on the linestring."""
        source = graph.nodes[edge.source]
        target = graph.nodes[edge.target]
        
        (_source_x, _source_y) = ctx.visual._graph_visual.ScalePositionToScreen((source.x, source.y))
        (_target_x, _target_y) = ctx.visual._graph_visual.ScalePositionToScreen((target.x, target.y))

        _width = screen.get_width()
        _height = screen.get_height()
        # Check points to cull
        if(_source_x < 0 and _target_x < 0) or (_source_x > _width and _target_x > _width):
            return
        if(_source_y < 0 and _target_y < 0) or (_source_y > _height and _target_y > _height ):
            return
        
        # If linestring is present, draw it as a curve
        if edge.linestring:
            #linestring[1:-1]
            linestring = [(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] + [(target.x, target.y)]
            scaled_points = [
                (ctx.visual._graph_visual.ScalePositionToScreen((x, y)))
                for x, y in linestring
            ]
            pygame.draw.aalines(screen, (0, 0, 0), False, scaled_points, 2)
        else:
            # Straight line
            source_position = (source.x, source.y)
            target_position = (target.x, target.y)
            (x1, y1) = ctx.visual._graph_visual.ScalePositionToScreen(source_position)
            (x2, y2) = ctx.visual._graph_visual.ScalePositionToScreen(target_position)

            pygame.draw.line(screen, (0, 0, 0), (int(x1), int(y1)), (int(x2), int(y2)), 2)

    @staticmethod
    def _draw_node(ctx, screen, node, color=(173, 255, 47)):
        position = (node.x, node.y)
        (x, y) = ctx.visual._graph_visual.ScalePositionToScreen(position)

        _width = screen.get_width()
        _height = screen.get_height()
        if (x < 0 or x > _width or y < 0 or y > _height):
            return
        
        pygame.draw.circle(screen, color, (int(x), int(y)), 4)  # Light greenish color
