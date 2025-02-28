from gamms.typing import IVisualizationEngine
from gamms.VisualizationEngine import Color, Space, Shape
from gamms.VisualizationEngine.graph_visual import GraphVisual
from gamms.VisualizationEngine.agent_visual import AgentVisual
from gamms.VisualizationEngine.render_manager import RenderManager
from gamms.VisualizationEngine.render_node import RenderNode
from gamms.context import Context
from gamms.typing.sensor_engine import SensorType

from typing import Dict, Any

import pygame


class PygameVisualizationEngine(IVisualizationEngine):
    def __init__(self, ctx, width=1980, height=1080, simulation_time_constant=2.0, **kwargs):
        pygame.init()
        self.ctx: Context = ctx
        self._width = width
        self._height = height
        self._sim_time_constant = simulation_time_constant
        self._graph_visual = None
        self._agent_visuals: dict[str, AgentVisual] = {}
        self._zoom = 1.0
        self._screen = pygame.display.set_mode((self._width, self._height), pygame.RESIZABLE)
        self._clock = pygame.time.Clock()
        self._default_font = pygame.font.Font(None, 36)
        self._waiting_user_input = False
        self._input_option_result = None
        self._waiting_agent_name = None
        self._waiting_simulation = False
        self._simulation_time = 0
        self._will_quit = False
        self._render_manager = RenderManager(ctx, 0, 0, 15, width, height)

    @property
    def width(self):
        return self._width
    
    @property
    def height(self):
        return self._height
    
    @property
    def screen(self):
        return self._screen
    
    @property
    def render_manager(self):
        return self._render_manager
    
    @property
    def waiting_agent_name(self):
        return self._waiting_agent_name
    
    def set_graph_visual(self, **kwargs):
        def graph_drawer(ctx, data):
            graph = data['graph']
            draw_id = data['draw_id']
            node_color = data['node_color']
            edge_color = data['edge_color']
            RenderManager.render_graph(ctx, graph, draw_id, node_color, edge_color)

        data = {}
        data['drawer'] = graph_drawer
        data['graph'] = self.ctx.graph.graph
        data['draw_id'] =kwargs.get('draw_id', False)
        data['node_color'] = kwargs.get('node_color', Color.LightGreen)
        data['edge_color'] = kwargs.get('edge_color', Color.Black)

        #Add data for node ID and Color
        self.add_artist('graph', data)

        self._graph_visual = GraphVisual(self.ctx.graph.graph, kwargs['width'], kwargs['height'])
        self._graph_visual.setRenderManager(self._render_manager)

        print("Successfully set graph visual")
    
    def set_agent_visual(self, name, **kwargs):
        agent = self.ctx.agent.get_agent(name)
        node = self.ctx.graph.graph.get_node(agent.current_node_id)
        self._agent_visuals[name] = (AgentVisual(name, (node.x, node.y), **kwargs))
        print(f"Successfully set agent visual for {name}")

        def agent_drawer(ctx, data):
            agent_visual = data['agent_visual']
            RenderManager.render_agent(ctx, agent_visual)

        data = {}
        data['drawer'] = agent_drawer
        data['agent_visual'] = self._agent_visuals[name]
        self.add_artist(name, data)
    
    def add_artist(self, name: str, data: Dict[str, Any]) -> None:
        if 'shape' not in data:
            # default to circle
            data['shape'] = Shape.Circle
    
        render_node = RenderNode(data)
        self._render_manager.add_render_node(name, render_node)
    
    def remove_artist(self, name):
        self._render_manager.remove_render_node(name)

    def handle_input(self):
        pressed_keys = pygame.key.get_pressed()
        scrollSpeed = self.render_manager.camera_size / 100
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            self._render_manager.camera_x += scrollSpeed #* self._clock.get_time() / 1000

        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            self._render_manager.camera_x -= scrollSpeed #* self._clock.get_time() / 1000

        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
            self._render_manager.camera_y -= scrollSpeed #* self._clock.get_time() / 1000

        if pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
            self._render_manager.camera_y += scrollSpeed #* self._clock.get_time() / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:

                if event.y > 0:
                    # self._camera.size /= 1.05
                    
                    self._render_manager.camera_size /= 1.05
                    self._zoom *= 1.05
                else:
                    # self._camera.size *= 1.05
                    self._render_manager.camera_size *= 1.05
                    self._zoom /= 1.05
                self._graph_visual.setZoom(self._zoom)
            if event.type == pygame.QUIT:
                self._will_quit = True
                self._input_option_result = -1
            if event.type == pygame.VIDEORESIZE:
                self._width = event.w
                self._height = event.h
                self._screen = pygame.display.set_mode((self._width, self._height), pygame.RESIZABLE)

            if self._waiting_user_input and event.type == pygame.KEYDOWN:
                if pygame.K_0 <= event.key <= pygame.K_9:
                    number_pressed = event.key - pygame.K_0
                    if number_pressed in self._input_options:
                        self._input_option_result = self._input_options[number_pressed]

    def handle_tick(self):
        self._clock.tick()
        if self._waiting_simulation:
            if self._simulation_time > self._sim_time_constant:
                self._waiting_simulation = False
                self._simulation_time = 0
            else:
                self._simulation_time += self._clock.get_time() / 1000
                alpha = self._simulation_time / self._sim_time_constant
                alpha = pygame.math.clamp(alpha, 0, 1)
                for agent in self.ctx.agent.create_iter():
                    self._agent_visuals[agent.name].update_simulation(alpha)

    def handle_single_draw(self):
        self._screen.fill(Color.White)

        # Note: Draw in layer order of back layer -> front layer
        # self._draw_grid()
        
        self.draw_input_overlay()
        self._render_manager.handle_render()
        self.draw_hud()

    def draw_input_overlay(self):
        
        if not self._waiting_user_input:
            return


        #FIXME: Testing for drawing

        for key_id, node_id in self._input_options.items():
            node = self.ctx.graph.graph.get_node(node_id)
            self._render_manager._draw_node(self.ctx, self._screen, node)

            self.ctx.visual._graph_visual.setNodeUIColor(node, (0, 255, 0))

            position = (node.x, node.y)
            (x, y) = self._graph_visual.ScalePositionToScreen(position)
            self.render_text(str(key_id), x, y, Space.Screen, Color.Black)

    def draw_hud(self):
        #FIXME: Add hud manager
        top = 10
        size_x, size_y = self.render_text("Some instructions here", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self.render_text(f"Camera size: {self._render_manager.camera_size:.2f}", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self.render_text(f"Current turn: {self._waiting_agent_name}", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self.render_text(f"FPS: {round(self._clock.get_fps(), 2)}", 10, top, Space.Screen)

    def cleanup(self):
        pygame.quit()

    def render_text(self, text: str, x: int, y: int, coord_space: Space=Space.World, color: tuple=Color.Black):
        if coord_space == Space.World:
            screen_x, screen_y = self._render_manager.world_to_screen(x, y)
        elif coord_space == Space.Screen:
            screen_x, screen_y = x, y
        elif coord_space == Space.Viewport:
            screen_x, screen_y = self._render_manager.viewport_to_screen(x, y)
        else:
            raise ValueError("Invalid coord_space value. Must be one of the values in the Space enum.")
        
        text_surface = self._default_font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(screen_x, screen_y))
        text_size = self._default_font.size(text)
        text_rect = text_rect.move(text_size[0] // 2, text_size[1] // 2)
        self._screen.blit(text_surface, text_rect)

        if coord_space == Space.World:
            return self._render_manager.screen_to_world_scale(text_size[0]), self._render_manager.screen_to_world_scale(text_size[1])
        elif coord_space == Space.Screen:
            return text_size
        elif coord_space == Space.Viewport:
            return self._render_manager.screen_to_viewport_scale(text_size[0]), self._render_manager.screen_to_viewport_scale(text_size[1])
        else:
            raise ValueError("Invalid coord_space value. Must be one of the values in the Space enum.")

    def render_rectangle(self, x: float, y: float, width: float, height: float, color: tuple=Color.Black):
        pygame.draw.rect(self._screen, color, pygame.Rect(x, y, width, height))

    def render_circle(self, x: float, y: float, radius: float, color: tuple=Color.Black):
        pygame.draw.circle(self._screen, color, (x, y), radius)

    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: tuple=Color.Black, width: int=1, isAA: bool=False):
        if isAA:
            pygame.draw.aaline(self._screen, color, (start_x, start_y), (end_x, end_y))
        else:
            pygame.draw.line(self._screen, color, (start_x, start_y), (end_x, end_y), width)

    def render_lines(self, points: list[tuple[float, float]], color: tuple=Color.Black, width: int=1, closed=False, isAA: bool=False):
        if isAA:
            pygame.draw.aalines(self._screen, color, closed, points)
        else:
            pygame.draw.lines(self._screen, color, closed, points, width)

    def render_line_to_surface(self, surface: pygame.Surface ,start_x: float, start_y: float, end_x: float, end_y: float, color: tuple=Color.Black, width: int=1, isAA: bool=False):
        if isAA:
            pygame.draw.aaline(surface, color, (start_x, start_y), (end_x, end_y))
        else:
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)

    def render_lines_to_surface(self, surface: pygame.Surface , points: list[tuple[float, float]], color: tuple=Color.Black, width: int=1, closed=False, isAA: bool=False):
        if isAA:
            pygame.draw.aalines(surface, color, closed, points)
        else:
            pygame.draw.lines(surface, color, closed, points, width)

    def render_polygon(self, points: list[tuple[float, float]], color: tuple=Color.Black, width: int=0):
        pygame.draw.polygon(self._screen, color, points, width)


    def rescale_surface(self, surface : pygame.Surface):
        center = surface.get_rect().center
        width, height = surface.get_size()

        width *= self._zoom
        height *= self._zoom

        scaled_surface = pygame.transform.scale(surface, (width, height))
        scaled_surface.get_rect(center=center)
        return scaled_surface
    
    def generate_graph_surface(self, lower_corner : tuple[float, float], upper_corner: tuple[float, float]):
        (x1, y1) = self._graph_visual.ScalePositionToScreen(lower_corner)
        (x2, y2) = self._graph_visual.ScalePositionToScreen(upper_corner)
        
        surfaceWidth = int(x2 - x1)
        surfaceHeight = int(y2 - y1)

        surface = pygame.Surface((surfaceWidth, surfaceHeight ))
        return surface

    def _draw_grid(self):
        x_min = self._render_manager.camera_x - self._render_manager.camera_size * 4
        x_max = self._render_manager.camera_x + self._render_manager.camera_size * 4
        y_min = self._render_manager.camera_y - self._render_manager.camera_size_y * 4
        y_max = self._render_manager.camera_y + self._render_manager.camera_size_y * 4
        step = 1
        for x in range(int(x_min), int(x_max) + 1, step):
            screen_start_x, screen_start_y = self._render_manager.world_to_screen(x, y_min)
            screen_end_x, screen_end_y = self._render_manager.world_to_screen(x, y_max)
            self.render_line(screen_start_x, screen_start_y, screen_end_x, screen_end_y, Color.LightGray, 3 if x % 5 == 0 else 1, False)

        for y in range(int(y_min), int(y_max) + 1, step):
            screen_start_x, screen_start_y = self._render_manager.world_to_screen(x_min, y)
            screen_end_x, screen_end_y = self._render_manager.world_to_screen(x_max, y)
            self.render_line(screen_start_x, screen_start_y, screen_end_x, screen_end_y, Color.LightGray, 3 if y % 5 == 0 else 1, False)

    def update(self):
        if self._will_quit:
            return
        
        self.handle_input()
        self.handle_single_draw()
        self.handle_tick()
        pygame.display.flip()
        

    def human_input(self, agent_name, state: Dict[str, Any]) -> int:
        if self.ctx.is_terminated():
            return state["curr_pos"]
        
        self._waiting_user_input = True

        def get_neighbours(state):
            for (type, data) in state["sensor"].values():
                if type == SensorType.NEIGHBOR:
                    return data
        current_agent = self.ctx.agent.get_agent(agent_name)
        
        self._waiting_agent_name = agent_name
        options: list[int] = get_neighbours(state)

        for node_id in options:
            if node_id != current_agent.current_node_id:
                self.ctx.visual._graph_visual.setEdgeUIColor(current_agent.current_node_id, node_id, (0, 255, 0))
                self.ctx.visual._graph_visual.setEdgeUIColor(node_id, current_agent.current_node_id, (0, 255, 0))

        self._input_options: dict[int, int] = {}
        for i in range(min(len(options), 10)):
            self._input_options[i] = options[i]

        while self._waiting_user_input:
            # still need to update the render
            self.update()

            result = self._input_option_result

            if result == -1:
                self.end_handle_human_input()
                self.ctx.terminate()
                return state["curr_pos"]
            
            if result is not None:
                self.end_handle_human_input()
                return result                

    def end_handle_human_input(self):
        self._waiting_user_input = False
        self._input_option_result = None
        self._waiting_agent_name = None
        self.ctx.visual._graph_visual.resetGraphUIColor()

    def simulate(self):
        self._waiting_simulation = True
        for agent in self.ctx.agent.create_iter():
            prev_node = self.ctx.graph.graph.get_node(agent.prev_node_id)
            target_node = self.ctx.graph.graph.get_node(agent.current_node_id)
            edges = self.ctx.graph.graph.get_edges()
            current_edge = None
            for _, edge in edges.items():
                if edge.source == agent.prev_node_id and edge.target == agent.current_node_id:
                    current_edge = edge
            
            self._agent_visuals[agent.name].start_simulation_lerp((prev_node.x, prev_node.y), (target_node.x, target_node.y), current_edge.linestring if current_edge is not None else None)

        while self._waiting_simulation and not self._will_quit:
            self.update()

    def handle_fog_of_war(self, agent_name, state: Dict[str, Any]):
        if self.ctx.is_terminated():
            return

        # Internal helper function
        def get_neighbours(state):
            for (type, data) in state["sensor"].values():
                if type == SensorType.NEIGHBOR:
                    return data

        current_agent = self.ctx.agent.get_agent(agent_name)
        options: list[int] = get_neighbours(state)

        for node_id in options:
            # Set node to not skip render
            self.ctx.visual._graph_visual.setNodeCull(node_id, False)
            self.ctx.visual._graph_visual.setNodeColor(node_id, (200, 200, 200))

            if node_id != current_agent.current_node_id:
                # Set to not skip render
                self.ctx.visual._graph_visual.setEdgeCull(current_agent.current_node_id, node_id, False)
                self.ctx.visual._graph_visual.setEdgeCull(node_id, current_agent.current_node_id, False)

                # Set color for fog of war
                
                self.ctx.visual._graph_visual.setEdgeColor(current_agent.current_node_id, node_id, (200, 200, 200))
                self.ctx.visual._graph_visual.setEdgeColor(node_id, current_agent.current_node_id, (200, 200, 200))

        return
    
    def clear_fog_of_war(self):
        if self.ctx.is_terminated():
            return
        
        self.ctx.visual._graph_visual.clearGraphCache()
        

    def terminate(self):
        self.cleanup()