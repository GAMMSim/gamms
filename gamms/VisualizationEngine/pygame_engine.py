from gamms.typing import IVisualizationEngine
from gamms.VisualizationEngine import Color, Space, Shape
from gamms.VisualizationEngine.camera import Camera
from gamms.VisualizationEngine.graph_visual import GraphVisual
from gamms.VisualizationEngine.agent_visual import AgentVisual
from gamms.VisualizationEngine.render_manager import RenderManager
from gamms.VisualizationEngine.Nodes.render_node import RenderNode
from gamms.context import Context
from gamms.typing.sensor_engine import SensorType

from typing import Dict, Any

import pygame


class PygameVisualizationEngine(IVisualizationEngine):
    def __init__(self, ctx, tick_callback = None, width=1980, height=1080, simulation_time_constant=2.0):
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
        self._camera = Camera(self, 0, 0, 15)
        self._tick_callback = tick_callback
        self._waiting_user_input = False
        self._input_option_result = None
        self._waiting_agent_name = None
        self._waiting_simulation = False
        self._simulation_time = 0
        self._will_quit = False
        self._render_manager = RenderManager(ctx)

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
    def waiting_agent_name(self):
        return self._waiting_agent_name
    
    def set_graph_visual(self, **kwargs):
        data = {}
        data['shape'] = Shape.Graph
        data['graph'] = self.ctx.graph.graph
        self.add_artist('graph', data)

        self._graph_visual = GraphVisual(self.ctx.graph.graph, kwargs['width'], kwargs['height'])
        self._graph_visual.setCamera(self._camera)

        print("Successfully set graph visual")
    
    def set_agent_visual(self, name, **kwargs):
        agent = self.ctx.agent.get_agent(name)
        node = self.ctx.graph.graph.get_node(agent.current_node_id)
        self._agent_visuals[name] = (AgentVisual(name, (node.x, node.y), **kwargs))
        print(f"Successfully set agent visual for {name}")

        data = {}
        data['shape'] = Shape.Agent
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
        for event in pygame.event.get():
            pressed_keys = pygame.key.get_pressed()
            # Multi key Event
            if pressed_keys[pygame.K_a] and pressed_keys[pygame.K_w]:
                self._camera.x += 1
                self._camera.y += -1
                return
            if pressed_keys[pygame.K_a] and pressed_keys[pygame.K_s]:
                self._camera.x += 1
                self._camera.y += 1
                return
            if pressed_keys[pygame.K_s] and pressed_keys[pygame.K_d]:
                self._camera.x += -1
                self._camera.y += 1
                return
            if pressed_keys[pygame.K_d] and pressed_keys[pygame.K_w]:
                self._camera.x += -1
                self._camera.y += -1
                return
            if pressed_keys[pygame.K_a] and pressed_keys[pygame.K_d]:
                return
            if pressed_keys[pygame.K_w] and pressed_keys[pygame.K_s]:
                return
            
            # Single Input Event
            if pressed_keys[pygame.K_a]:
                self._camera.x += 1
                self._camera.y += 0
                return
            if pressed_keys[pygame.K_s]:
                self._camera.x += 0
                self._camera.y += 1
                return
            if pressed_keys[pygame.K_d]:
                self._camera.x += -1
                self._camera.y += 0
                return
            if pressed_keys[pygame.K_w]:
                self._camera.x += 0
                self._camera.y += -1
                return
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self._camera.size /= 1.05
                    if(self._camera.size > 2):
                        self._zoom *= 1.05
                        self._zoom = self._graph_visual.setZoom(self._zoom)
                else:
                    self._camera.size *= 1.05
                    if(self._camera.size < 350):
                        self._zoom /= 1.05
                        self._zoom = self._graph_visual.setZoom(self._zoom)
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
        self._draw_grid()

        self._render_manager.handle_render()
        
        self.draw_input_overlay()
        self.draw_hud()

    def draw_input_overlay(self):
        if not self._waiting_user_input:
            return
        
        for key_id, node_id in self._input_options.items():
            node = self.ctx.graph.graph.get_node(node_id)
            self._render_manager._draw_node(self.ctx, self._screen, node)

            position = (node.x, node.y)
            (x, y) = self._graph_visual.ScalePositionToScreen(position)
            self.render_text(str(key_id), x, y, Space.Screen, Color.Black)

    def draw_hud(self):
        #FIXME: Add hud manager
        top = 10
        size_x, size_y = self.render_text("Some instructions here", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self.render_text(f"Camera size: {self._camera.size:.2f}", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self.render_text(f"Current turn: {self._waiting_agent_name}", 10, top, Space.Screen)

    def cleanup(self):
        pygame.quit()

    def render_text(self, text: str, x: int, y: int, coord_space: Space=Space.World, color: tuple=Color.Black):
        if coord_space == Space.World:
            screen_x, screen_y = self._camera.world_to_screen(x, y)
        elif coord_space == Space.Screen:
            screen_x, screen_y = x, y
        elif coord_space == Space.Viewport:
            screen_x, screen_y = self._camera.viewport_to_screen(x, y)
        else:
            raise ValueError("Invalid coord_space value. Must be one of the values in the Space enum.")
        
        text_surface = self._default_font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(screen_x, screen_y))
        text_size = self._default_font.size(text)
        text_rect = text_rect.move(text_size[0] // 2, text_size[1] // 2)
        self._screen.blit(text_surface, text_rect)

        if coord_space == Space.World:
            return self._camera.screen_to_world_scale(text_size[0]), self._camera.screen_to_world_scale(text_size[1])
        elif coord_space == Space.Screen:
            return text_size
        elif coord_space == Space.Viewport:
            return self._camera.screen_to_viewport_scale(text_size[0]), self._camera.screen_to_viewport_scale(text_size[1])
        else:
            raise ValueError("Invalid coord_space value. Must be one of the values in the Space enum.")

    def render_rectangle(self, x: float, y: float, width: float, height: float, color: tuple=Color.Black):
        screen_x, screen_y = self._camera.world_to_screen(x, y)
        screen_width = self._camera.world_to_screen_scale(width)
        screen_height = self._camera.world_to_screen_scale(height)
        pygame.draw.rect(self._screen, color, pygame.Rect(screen_x, screen_y, screen_width, screen_height))


    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: tuple=Color.Black, width: int=1, isAA: bool=False):
        screen_start_x, screen_start_y = self._camera.world_to_screen(start_x, start_y)
        screen_end_x, screen_end_y = self._camera.world_to_screen(end_x, end_y)
        if isAA:
            pygame.draw.aaline(self._screen, color, (screen_start_x, screen_start_y), (screen_end_x, screen_end_y))
        else:
            pygame.draw.line(self._screen, color, (screen_start_x, screen_start_y), (screen_end_x, screen_end_y), width)

    def _draw_grid(self):
        x_min = self._camera.x - self._camera.size * 4
        x_max = self._camera.x + self._camera.size * 4
        y_min = self._camera.y - self._camera.size_y * 4
        y_max = self._camera.y + self._camera.size_y * 4
        step = 1
        for x in range(int(x_min), int(x_max) + 1, step):
            self.render_line(x, y_min, x, y_max, Color.LightGray, 3 if x % 5 == 0 else 1, False)

        for y in range(int(y_min), int(y_max) + 1, step):
            self.render_line(x_min, y, x_max, y, Color.LightGray, 3 if y % 5 == 0 else 1, False)

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

        self._waiting_agent_name = agent_name
        options: list[int] = get_neighbours(state)
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

    def terminate(self):
        self.cleanup()