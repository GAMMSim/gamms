from gamms.VisualizationEngine import Color, Shape
from gamms.VisualizationEngine.render_node import RenderNode
from gamms.VisualizationEngine.builtin_artists import AgentData, GraphData
from gamms.context import Context
import math


class RenderManager:
    def __init__(self, ctx: Context, camera_x: float, camera_y: float, camera_size: float, screen_width: int, screen_height: int):
        self.ctx: Context = ctx

        self._screen_width = screen_width
        self._screen_height = screen_height
        self._aspect_ratio = self._screen_width / self._screen_height

        self._camera_x = camera_x
        self._camera_y = camera_y
        self._camera_size = camera_size
        self._camera_size_y = camera_size / self.aspect_ratio

        self._update_bounds()

        self._render_nodes: dict[str, RenderNode] = {}
        self._graph_center = (0, 0)

    def _update_bounds(self):
        self._bound_left = -self.camera_size + self.camera_x
        self._bound_right = self.camera_size + self.camera_x
        self._bound_top = -self.camera_size_y + self.camera_y
        self._bound_bottom = self.camera_size_y + self.camera_y

    @property
    def camera_x(self):
        return self._camera_x
    
    @camera_x.setter
    def camera_x(self, value: float):
        self._camera_x = value
        self._update_bounds()

    @property
    def camera_y(self):
        return self._camera_y
    
    @camera_y.setter
    def camera_y(self, value: float):
        self._camera_y = value
        self._update_bounds()

    @property
    def camera_size(self):
        """
        The orthographic size of the camera represents half the width of the camera view.

        Returns:
            float: The orthographic size.
        """
        return self._camera_size
    
    @camera_size.setter
    def camera_size(self, value: float):
        self._camera_size = value
        self._camera_size_y = self.camera_size / self.aspect_ratio
        self._update_bounds()
    
    @property
    def camera_size_y(self):
        """
        The orthographic size of the camera represents half the height of the camera view.

        Returns:
            float: The verticle orthographic size.
        """
        return self._camera_size_y
    
    @property
    def screen_width(self):
        return self._screen_width

    @screen_width.setter
    def screen_width(self, value: int):
        self._screen_width = value
        self._aspect_ratio = self._screen_width / self._screen_height
    
    @property
    def screen_height(self):
        return self._screen_height

    @screen_height.setter
    def screen_height(self, value: int):
        self._screen_height = value
        self._aspect_ratio = self._screen_width / self._screen_height
    
    @property
    def aspect_ratio(self):
        return self._aspect_ratio

    def world_to_screen_scale(self, world_size: float) -> float:
        """
        Transforms a world size to a screen size.
        """
        return world_size / self.camera_size * self.screen_width
    
    def screen_to_world_scale(self, screen_size: float) -> float:
        """
        Transforms a screen size to a world size.
        """
        return screen_size / self.screen_width * self.camera_size
    
    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a world coordinate to a screen coordinate.
        """
        x -= self.camera_x
        y -= self.camera_y
        screen_x = (x + self.camera_size) / (2 * self.camera_size) * self.screen_width
        screen_y = (-y + self.camera_size_y) / (2 * self.camera_size_y) * self.screen_height
        return screen_x, screen_y
    
    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a screen coordinate to a world coordinate.
        """
        world_x = x / self.screen_width * 2 * self.camera_size - self.camera_size
        world_y = -y / self.screen_height * 2 * self.camera_size_y + self.camera_size_y
        return world_x, world_y
    
    def viewport_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a viewport coordinate to a screen coordinate.
        """
        screen_x = x * self.screen_width
        screen_y = y * self.screen_height
        return screen_x, screen_y
    
    def screen_to_viewport(self, x: float, y: float) -> tuple[float, float]:
        """
        Transforms a screen coordinate to a viewport coordinate.
        """
        viewport_x = x / self.screen_width
        viewport_y = y / self.screen_height
        return viewport_x, viewport_y
    
    def viewport_to_screen_scale(self, viewport_size: float) -> float:
        """
        Transforms a viewport size to a screen size.
        """
        return viewport_size * self.screen_width
    
    def screen_to_viewport_scale(self, screen_size: float) -> float:
        """
        Transforms a screen size to a viewport size.
        """
        return screen_size / self.screen_width

    def set_graph_center(self, graph_center):
        self._graph_center = graph_center
        self._camera_x = graph_center[0]
        self._camera_y = graph_center[1]

    def scale_to_screen(self, position) -> tuple[float, float]:
        # map_position = ((position[0] - self._graph_center[0]), (position[1] - self._graph_center[1]))
        map_position = position
        map_position = self.world_to_screen(map_position[0], map_position[1])
        return map_position

    def check_circle_culled(self, x, y, radius):
        return (x + radius < self._bound_left or x - radius > self._bound_right or
                y + radius < self._bound_top or y - radius > self._bound_bottom)

    def check_rectangle_culled(self, x, y, width, height):
        return (x - width / 2 > self._bound_right or x + width / 2 < self._bound_left or
                y - height / 2 > self._bound_bottom or y + height / 2 < self._bound_top)

    def check_line_culled(self, x1, y1, x2, y2):
        return (x1 < self._bound_left and x2 < self._bound_left or x1 > self._bound_right and x2 > self._bound_right or
                y1 < self._bound_top and y2 < self._bound_top or y1 > self._bound_bottom and y2 > self._bound_bottom)

    def check_lines_culled(self, points):
        source = points[0]
        target = points[-1]
        return self.check_line_culled(source[0], source[1], target[0], target[1])

    def check_polygon_culled(self, points):
        for point in points:
            if self._bound_left <= point[0] <= self._bound_right and self._bound_top <= point[1] <= self._bound_bottom:
                return False

        return True

    def add_artist(self, name: str, data: dict):
        """
        Add an artist to the render manager. An artist can draw one or more shapes on the screen and may have a customized drawer.

        Args:
            name (str): The unique name of the artist.
            data (dict): A dictionary containing the artist's data.
        """
        render_node = RenderNode(data)
        self._render_nodes[name] = render_node

    def remove_artist(self, name: str):
        """
        Remove an artist from the render manager.

        Args:
            name (str): The unique name of the artist to remove.
        """
        if name in self._render_nodes:
            del self._render_nodes[name]
        else:
            print(f"Warning: Artist {name} not found.")

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
            elif shape == Shape.Rectangle:
                RenderManager.render_rectangle(self.ctx, render_node.x, render_node.y, render_node.data['width'], render_node.data['height'], render_node.color)
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
            color (tuple, optional): The color of the circle. Defaults to Color.Black.
        """
        (x, y) = ctx.visual._render_manager.scale_to_screen((x, y))

        _width = ctx.visual._render_manager.screen_width
        _height = ctx.visual._render_manager.screen_height
        if x < 0 or x > _width or y < 0 or y > _height:
            return

        ctx.visual.render_circle(x, y, radius, color)

    @staticmethod
    def render_rectangle(ctx: Context, x: float, y: float, width: float, height: float, color: tuple=Color.Black):
        """
        Render a rectangle at the given position with the given width, height, and color.

        Args:
            ctx (Context): The current simulation context.
            x (float): The x coordinate of the rectangle's center.
            y (float): The y coordinate of the rectangle's center.
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
            color (tuple, optional): The color of the rectangle. Defaults to Color.Black.
        """
        # render_manager = ctx.visual.render_manager
        (x, y) = ctx.visual._render_manager.scale_to_screen((x, y))
        # scaled_width = ctx.visual.render_manager.world_to_screen_scale(width)

        ctx.visual.render_rectangle(x, y, width, height, color)

    @staticmethod
    def render_agent(ctx: Context, agent_data: AgentData):
        """
        Render an agent as a triangle at its current position on the screen. This is the default rendering method for agents.

        Args:
            ctx (Context): The current simulation context.
            agent_data (AgentData): The agent to render.
        """
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

        # (scaled_x, scaled_y) = ctx.visual._render_manager.scale_to_screen(position)
        (scaled_x, scaled_y) = position

        # Draw each agent as a triangle at its current position
        angle = math.radians(45)
        point1 = (scaled_x + size * math.cos(angle), scaled_y + size * math.sin(angle))
        point2 = (scaled_x + size * math.cos(angle + 2.5), scaled_y + size * math.sin(angle + 2.5))
        point3 = (scaled_x + size * math.cos(angle - 2.5), scaled_y + size * math.sin(angle - 2.5))

        ctx.visual.render_polygon([point1, point2, point3], color)

    @staticmethod
    def render_graph(ctx: Context, graph_data: GraphData):
        """
        Render the graph by drawing its nodes and edges on the screen. This is the default rendering method for graphs.

        Args:
            ctx (Context): The current simulation context.
            graph_data (GraphData): The graph to render.
        """
        graph = ctx.graph.graph
        node_color = graph_data.node_color
        edge_color = graph_data.edge_color
        draw_id = graph_data.draw_id
        for edge in graph.get_edges().values():
            RenderManager._draw_edge(ctx, graph, edge, edge_color)
        for node in graph.get_nodes().values():
            RenderManager._draw_node(ctx, node, node_color, draw_id)

    @staticmethod
    def _draw_edge(ctx, graph, edge, edge_color):
        """Draw an edge as a curve or straight line based on the linestring."""
        source = graph.get_node(edge.source)
        target = graph.get_node(edge.target)

        color = edge_color
        if ctx.visual._waiting_agent_name:
            current_waiting_agent = ctx.agent.get_agent(ctx.visual._waiting_agent_name)
            target_node_id_list = ctx.visual._input_options.values()
            if current_waiting_agent is not None and edge.source == current_waiting_agent.current_node_id and edge.target in target_node_id_list:
                color = (0, 255, 0)

        # If linestring is present, draw it as a curve
        if edge.linestring:
            #linestring[1:-1]
            linestring = [(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] + [(target.x, target.y)]
            ctx.visual.render_lines(linestring, color, is_aa=True)
        else:
            # Straight line
            ctx.visual.render_line(source.x, source.y, target.x, target.y, color, 2)

    @staticmethod
    def _draw_node(ctx, node, node_color=(169, 169, 169), draw_id=False):
        # color = ctx.visual._graph_visual.getNodeColorById(node.id)
        if node.id in ctx.visual._input_options.values():
            color = (0, 255, 0)
            scale = 8
        else:
            color = node_color
            scale = 4

        ctx.visual.render_circle(node.x, node.y, scale, color)

        if draw_id:
            ctx.visual.render_text(str(node.id), node.x, node.y + 10, (0, 0, 0))
