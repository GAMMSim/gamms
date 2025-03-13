from gamms.typing import IVisualizationEngine
from gamms.VisualizationEngine import Color, Space, Shape
from gamms.VisualizationEngine.render_manager import RenderManager
from gamms.VisualizationEngine.builtin_artists import AgentData, GraphData
from gamms.VisualizationEngine.default_drawers import render_agent, render_graph, render_neighbor_sensor, render_map_sensor, render_agent_sensor
from gamms.context import Context
from gamms.typing.sensor_engine import SensorType

from typing import Dict, Any

import pygame


class PygameVisualizationEngine(IVisualizationEngine):
    def __init__(self, ctx, width=1280, height=720, simulation_time_constant=2.0, **kwargs):
        pygame.init()
        self.ctx: Context = ctx
        self._sim_time_constant = simulation_time_constant
        self._screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self._clock = pygame.time.Clock()
        self._default_font = pygame.font.Font(None, 36)
        self._waiting_user_input = False
        self._input_option_result = None
        self._waiting_agent_name = None
        self._waiting_simulation = False
        self._simulation_time = 0
        self._will_quit = False
        self._render_manager = RenderManager(ctx, 0, 0, 15, width, height)
        self._surface_dict : dict[int, pygame.Surface ] = {}
        self._scaled_surface_cache: dict[int, pygame.Surface] = {}
    
    def create_layer(self, layer_id: int, width : int, height : int) -> int:
        if layer_id is None:
            layer_id = 0

        if layer_id not in self._surface_dict:
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            self._surface_dict[layer_id] = surface

        # Order layers by ascending order
        self._surface_dict = {id: self._surface_dict[id] for id in sorted(self._surface_dict.keys())}

        return layer_id

    #FIXME: add layer as a optional argument
    def set_graph_visual(self, **kwargs):
        graph = self.ctx.graph.graph
        x_list = [node.x for node in graph.get_nodes().values()]
        y_list = [node.y for node in graph.get_nodes().values()]
        x_min = min(x_list)
        x_max = max(x_list)
        y_min = min(y_list)
        y_max = max(y_list)
        x_mean = sum(x_list) / len(x_list) if len(x_list) > 0 else 0
        y_mean = sum(y_list) / len(y_list) if len(y_list) > 0 else 0
        self._render_manager.set_origin(x_mean, y_mean, x_max - x_min, y_max - y_min)
        self._render_manager.camera_size = max(x_max - x_min, y_max - y_min)
        layer_id = self.create_layer(10, 3000, 3000)

        #FIXME: add some way to let layer_ID be = None
        graph_data = GraphData(node_color=kwargs.get('node_color', Color.LightGreen),
                               edge_color=kwargs.get('edge_color', Color.Black), 
                               draw_id=kwargs.get('draw_id', False),
                               layer = layer_id)

        data = {}
        data['drawer'] = render_graph
        data['layer'] = 10
        data['graph_data'] = graph_data
        data['single_render'] = True

        #Add data for node ID and Color
        self.add_artist('graph', data)

        render_graph(self.ctx, data)
    
    def set_agent_visual(self, name, **kwargs):
        # layer_id = self.create_layer(20, 3000, 3000)
        
        agent_data = AgentData(name=name, color=kwargs.get('color', Color.Black), size=kwargs.get('size', 8))
        data = {}
        data['drawer'] = render_agent
        data['layer'] = 20
        data['agent_data'] = agent_data

        self.add_artist(name, data)

    def set_sensor_visual(self, sensor_name, **kwargs):
        sensor = self.ctx.sensor.get_sensor(sensor_name)
        sensor_type = sensor.type
        data = {}
        data['sensor'] = sensor
        data['layer'] = kwargs.get('layer', 30)
        if sensor_type == SensorType.NEIGHBOR:
            data['drawer'] = render_neighbor_sensor
            data['color'] = kwargs.get('color', Color.Cyan)
            data['size'] = kwargs.get('size', 8)
        elif sensor_type == SensorType.MAP or sensor_type == SensorType.RANGE or sensor_type == SensorType.ARC:
            data['drawer'] = render_map_sensor
            data['node_color'] = kwargs.get('node_color', Color.LightGreen)
            data['edge_color'] = kwargs.get('edge_color', Color.Cyan)
        elif sensor_type == SensorType.AGENT or sensor_type == SensorType.AGENT_RANGE or sensor_type == SensorType.AGENT_ARC:
            data['drawer'] = render_agent_sensor
            data['color'] = kwargs.get('color', Color.Cyan)
            data['size'] = kwargs.get('size', 8)
        else:
            raise ValueError(f"Invalid sensor type: {sensor_type}")

        self.add_artist(f'sensor_{sensor_name}', data)
    
    def add_artist(self, name: str, data: Dict[str, Any]) -> None:
        if 'drawer' not in data and 'shape' not in data:
            # default to circle
            data['shape'] = Shape.Circle

        layer = data.get('layer', 30)
        single_render = data.get('single_render', False)
        if layer not in self._surface_dict and single_render:
            self.create_layer(layer, 3000, 3000)

        print("add_artist():self._surface_dict: ", self._surface_dict)
        self._render_manager.add_artist(name, data)
    
    def remove_artist(self, name):
        self._render_manager.remove_artist(name)

    def handle_input(self):
        pressed_keys = pygame.key.get_pressed()
        scroll_speed = self._render_manager.camera_size / 2
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            self._render_manager.camera_x -= scroll_speed * self._clock.get_time() / 1000

        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            self._render_manager.camera_x += scroll_speed * self._clock.get_time() / 1000

        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
            self._render_manager.camera_y += scroll_speed * self._clock.get_time() / 1000

        if pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
            self._render_manager.camera_y -= scroll_speed * self._clock.get_time() / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    if self._render_manager.camera_size > 2:
                        self._render_manager.camera_size /= 1.05
                else:
                    self._render_manager.camera_size *= 1.05

                self._scaled_surface_cache.clear()
            if event.type == pygame.QUIT:
                self._will_quit = True
                self._input_option_result = -1
            if event.type == pygame.VIDEORESIZE:
                self._render_manager.screen_width = event.w
                self._render_manager.screen_height = event.h
                self._screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

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
        
        for key_id, node_id in self._input_options.items():
            node = self.ctx.graph.graph.get_node(node_id)
            (x, y) = self._render_manager.world_to_screen(node.x, node.y)
            self._render_text_internal(str(key_id), x, y, Space.Screen, Color.Black)

    def draw_hud(self):
        #FIXME: Add hud manager
        top = 10
        size_x, size_y = self._render_text_internal("Some instructions here", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self._render_text_internal(f"Camera size: {self._render_manager.camera_size:.2f}", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self._render_text_internal(f"Current turn: {self._waiting_agent_name}", 10, top, Space.Screen)
        top += size_y + 10
        size_x, size_y = self._render_text_internal(f"FPS: {round(self._clock.get_fps(), 2)}", 10, top, Space.Screen)


    def _render_text_internal(self, text: str, x: float, y: float, coord_space: Space=Space.World, color: tuple=Color.Black):
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
        
    def _get_target_surface(self, layer: int):
        if layer >= 0:
            return self._surface_dict[layer]
        else:
            return self._screen

    def render_text(self, text: str, x: float, y: float, color: tuple = Color.Black, layer = -1, perform_culling_test: bool=True):
        text_size = self._default_font.size(text)
        if perform_culling_test and self._render_manager.check_rectangle_culled(x, y, text_size[0], text_size[1]):
            return

        (x, y) = self._render_manager.world_to_screen(x, y, layer)
        text_surface = self._default_font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        text_rect.move_ip(text_size[0] / 2, text_size[1] / 2)

        surface = self._get_target_surface(layer)
        surface.blit(text_surface, text_rect)

    def render_rectangle(self, x: float, y: float, width: float, height: float, color: tuple=Color.Black, layer = -1,
                         perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_rectangle_culled(x, y, width, height):
            return

        (x, y) = self._render_manager.world_to_screen(x, y, layer)

        surface = self._get_target_surface(layer)
        pygame.draw.rect(surface, color, pygame.Rect(x, y, width, height))

    def render_circle(self, x: float, y: float, radius: float, color: tuple=Color.Black, layer = -1,
                      perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_circle_culled(x, y, radius):
            return

        (x, y) = self._render_manager.world_to_screen(x, y, layer)
        radius = self._render_manager.world_to_screen_scale(radius)

        surface = self._get_target_surface(layer)
        pygame.draw.circle(surface, color, (x, y), radius)

    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: tuple=Color.Black,
                    width: int=1, layer = -1, is_aa: bool=False, perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_line_culled(start_x, start_y, end_x, end_y):
            return

        (start_x, start_y) = self._render_manager.world_to_screen(start_x, start_y, layer)
        (end_x, end_y) = self._render_manager.world_to_screen(end_x, end_y, layer)

        surface = self._get_target_surface(layer)
        if is_aa:
            pygame.draw.aaline(surface, color, (start_x, start_y), (end_x, end_y))
        else:
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)

    def render_lines(self, points: list[tuple[float, float]], color: tuple=Color.Black, width: int=1, layer = -1, closed=False,
                     is_aa: bool=False, perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_lines_culled(points):
            return

        points = [self._render_manager.world_to_screen(point[0], point[1], layer) for point in points]

        surface = self._get_target_surface(layer)
        if is_aa:
            pygame.draw.aalines(surface, color, closed, points)
        else:
            pygame.draw.lines(surface, color, closed, points, width)

    def render_polygon(self, points: list[tuple[float, float]], color: tuple=Color.Black, width: int=0, layer = -1,
                       perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_polygon_culled(points):
            return

        points = [self._render_manager.world_to_screen(point[0], point[1], layer) for point in points]

        surface = self._get_target_surface(layer)
        pygame.draw.polygon(surface, color, points, width)

    def fill_layer(self, layer_id: int, color: tuple):
        if layer_id in self._surface_dict:
            self._surface_dict[layer_id].fill(color)

    def render_layer(self, layer_id: int, left: float, top: float, width: float, height: float):
        if layer_id in self._surface_dict:
            surface = self._surface_dict[layer_id]

            if layer_id not in self._scaled_surface_cache:
                scaled_surface = pygame.transform.scale(surface, (width, height))
                self._scaled_surface_cache[layer_id] = scaled_surface

            self._screen.blit(self._scaled_surface_cache[layer_id], (left, top))

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
                
        # current_agent = self.ctx.agent.get_agent(agent_name)
        
        self._waiting_agent_name = agent_name
        options = get_neighbours(state)
        # options: list[int] = [edge.target for edge in edges]

        # for node_id in options:
        #     if node_id != current_agent.current_node_id:
        #         self.ctx.visual._graph_visual.setEdgeColor(current_agent.current_node_id, node_id, (0, 255, 0))
        #         self.ctx.visual._graph_visual.setEdgeColor(node_id, current_agent.current_node_id, (0, 255, 0))

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
        # self.ctx.visual._graph_visual.resetGraphColor()

    def simulate(self):
        self._waiting_simulation = True
        self._simulation_time = 0

        while self._waiting_simulation and not self._will_quit:
            self.update()

    def terminate(self):
        pygame.quit()