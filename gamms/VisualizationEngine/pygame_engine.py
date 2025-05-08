from gamms.VisualizationEngine import Color, Space, Shape, Artist, lazy
from gamms.VisualizationEngine.render_manager import RenderManager
from gamms.VisualizationEngine.builtin_artists import AgentData, GraphData
from gamms.VisualizationEngine.default_drawers import render_circle, render_rectangle, \
    render_agent, render_graph, render_neighbor_sensor, render_map_sensor, render_agent_sensor, render_input_overlay
from gamms.typing import (
    IVisualizationEngine,
    IArtist,
    ArtistType,
    IContext,
    SensorType, 
    OpCodes,
    ColorType
)
from typing import Dict, Any, List, Tuple, Union, cast

class PygameVisualizationEngine(IVisualizationEngine):
    def __init__(self, ctx: IContext, width: int = 1280, height: int = 720, simulation_time_constant: float = 2.0, **kwargs : Dict[str, Any]):
        pygame = lazy('pygame')
        repr(pygame)
        try:
            self._pygame = pygame.pygame
        except AttributeError:
            self._pygame = pygame
        self._pygame.init()
        self.ctx: IContext = ctx
        self._sim_time_constant = simulation_time_constant
        self._screen = self._pygame.display.set_mode((width, height), self._pygame.RESIZABLE)
        self._clock = self._pygame.time.Clock()
        self._default_font = self._pygame.font.Font(None, 36)
        self._waiting_user_input = False
        self._input_option_result = None
        self._waiting_agent_name = None
        self._waiting_simulation = False
        self._simulation_time = 0
        self._will_quit = False
        self._render_manager = RenderManager(ctx, 0, 0, 15, width, height)
        self._surface_dict : Dict[int, self._pygame.Surface ] = {}
        self._agent_artists: Dict[str, IArtist] = {}
        self._graph_artists: Dict[str, IArtist] = {}

        input_overlay_args = kwargs.get('input_overlay', {})
        self._input_overlay_artist = self._set_input_overlay_artist(input_overlay_args)
    
    def create_layer(self, layer_id: int, width : int, height : int) -> int:
        if layer_id not in self._surface_dict:
            surface = self._pygame.Surface((width, height), self._pygame.SRCALPHA)
            self._surface_dict[layer_id] = surface

        # Order layers by ascending order
        self._surface_dict = {id: self._surface_dict[id] for id in sorted(self._surface_dict.keys())}

        return layer_id

    def set_graph_visual(self, **kwargs: Dict[str, Any]) -> IArtist:
        x_list: List[float] = []
        y_list: List[float] = []
        for node_id in self.ctx.graph.graph.get_nodes():
            node = self.ctx.graph.graph.get_node(node_id)
            x_list.append(node.x)
            y_list.append(node.y)
        x_min = min(x_list, default=0.0)
        x_max = max(x_list, default=0.0)
        y_min = min(y_list, default=0.0)
        y_max = max(y_list, default=0.0)
        x_mean = sum(x_list) / len(x_list) if len(x_list) > 0 else 0
        y_mean = sum(y_list) / len(y_list) if len(y_list) > 0 else 0

        self._render_manager.set_origin(x_mean, y_mean, x_max - x_min, y_max - y_min)
        self._render_manager.camera_size = max(x_max - x_min, y_max - y_min, 0.1)

        width = self._render_manager.screen_width
        height = self._render_manager.screen_height
        
        self.create_layer(10, width, height)
        
        graph_data = GraphData(node_color=cast(ColorType, kwargs.get('node_color', Color.DarkGray)),
                               node_size=cast(int, kwargs.get('node_size', 2)),
                               edge_color=cast(ColorType, kwargs.get('edge_color', Color.LightGray)), 
                               draw_id=cast(bool, kwargs.get('draw_id', False)))

        artist = Artist(self.ctx, render_graph, 10)
        artist.data['graph_data'] = graph_data
        artist.set_will_draw(False)
        artist.set_artist_type(ArtistType.GRAPH)

        #Add data for node ID and Color
        self.add_artist('graph', artist)

        # Trigger the redraw of the graph artists after it has been added
        self._redraw_graph_artists()

        return artist

    def _set_input_overlay_artist(self, args: Dict[str, Any]) -> IArtist:
        graph_data = GraphData(node_color = args.get('node_color', Color.Green),
                               node_size = args.get('node_size', 4),
                               edge_color = args.get('edge_color', Color.Green),
                               draw_id = False)

        artist = Artist(self.ctx, render_input_overlay, 50)
        artist.data['_input_options'] = {}
        artist.data['_waiting_agent_name'] = None
        artist.data['_waiting_user_input'] = False
        artist.data['graph_data'] = graph_data
        artist.set_visible(False)

        self.add_artist('input_overlay', artist)        
        
        return artist
    
    def set_agent_visual(self, name: str, **kwargs: Dict[str, Any]) -> IArtist:
        
        agent_data = AgentData(
            name=name,
            color=cast(ColorType, kwargs.get('color', Color.Black)),
            size=cast(int,kwargs.get('size', 8))
        )

        artist = Artist(self.ctx, render_agent, 20)
        artist.data['agent_data'] = agent_data
        artist.set_artist_type(ArtistType.AGENT)
        artist.data['_alpha'] = 1.0

        self.add_artist(name, artist)

        return artist

    def set_sensor_visual(self, name: str, **kwargs: Dict[str, Any]) -> IArtist:
        sensor = self.ctx.sensor.get_sensor(name)
        sensor_type = sensor.type

        data: Dict[str, Any] = {
            'name': sensor.sensor_id,
        }

        if sensor_type == SensorType.NEIGHBOR:
            drawer = render_neighbor_sensor
            data['color'] = kwargs.pop('color', Color.Cyan)
            data['size'] = kwargs.pop('size', 8)
        elif sensor_type == SensorType.MAP or sensor_type == SensorType.RANGE or sensor_type == SensorType.ARC:
            drawer = render_map_sensor
            data['node_color'] = kwargs.pop('node_color', Color.Cyan)
            data['edge_color'] = kwargs.pop('edge_color', Color.Cyan)
        elif sensor_type == SensorType.AGENT or sensor_type == SensorType.AGENT_RANGE or sensor_type == SensorType.AGENT_ARC:
            drawer = render_agent_sensor
            data['color'] = kwargs.pop('color', Color.Cyan)
            data['size'] = kwargs.pop('size', 8)
        else:
            raise ValueError(f"Invalid sensor type: {sensor_type}")
        
        layer = cast(int, kwargs.pop('layer', 30))
        artist = Artist(self.ctx, drawer, layer)
        artist.data.update(data)
        
        self.add_artist(f'sensor_{name}', artist)

        return artist
    
    def add_artist(self, name: str, artist: Union[IArtist, Dict[str, Any]]) -> IArtist:
        if isinstance(artist, IArtist):
            artist_to_add = artist
        else:
            shape = artist.get('shape', None)
            drawer = artist.get('drawer', None)
            layer = artist.get('layer', 30)

            if shape is not None and drawer is not None:
                self.ctx.logger.warning(f"Both shape and drawer are set for artist {name}, will use drawer.")

            if drawer is None and shape is not None:
                drawer = shape
            else:
                drawer = Shape.Circle

            artist_to_add = Artist(self.ctx, drawer, layer)
            artist_to_add.data = artist

        layer = artist_to_add.get_layer()
        if artist_to_add.get_artist_type() == ArtistType.AGENT:
            self._agent_artists[name] = artist_to_add
        elif artist_to_add.get_artist_type() == ArtistType.GRAPH:
            self._graph_artists[name] = artist_to_add
            
        self._render_manager.add_artist(name, artist_to_add)
        return artist_to_add

    def remove_artist(self, name: str):
        self._render_manager.remove_artist(name)

    def handle_input(self):
        pressed_keys = self._pygame.key.get_pressed()
        scroll_speed = self._render_manager.camera_size / 2
        if pressed_keys[self._pygame.K_a] or pressed_keys[self._pygame.K_LEFT]:
            self._render_manager.camera_x -= (scroll_speed * self._clock.get_time() / 1000)
            self._redraw_graph_artists()

        if pressed_keys[self._pygame.K_d] or pressed_keys[self._pygame.K_RIGHT]:
            self._render_manager.camera_x += (scroll_speed * self._clock.get_time() / 1000)
            self._redraw_graph_artists()

        if pressed_keys[self._pygame.K_w] or pressed_keys[self._pygame.K_UP]:
            self._render_manager.camera_y += (scroll_speed * self._clock.get_time() / 1000)
            self._redraw_graph_artists()

        if pressed_keys[self._pygame.K_s] or pressed_keys[self._pygame.K_DOWN]:
            self._render_manager.camera_y -= (scroll_speed * self._clock.get_time() / 1000)
            self._redraw_graph_artists()
        
        for event in self._pygame.event.get():
            if event.type == self._pygame.MOUSEWHEEL:
                if event.y > 0:
                    if self._render_manager.camera_size > 2:
                        self._render_manager.camera_size /= 1.05
                else:
                    self._render_manager.camera_size *= 1.05
                    
                self._redraw_graph_artists()

            if event.type == self._pygame.QUIT:
                self._will_quit = True
                self._input_option_result = -1
            if event.type == self._pygame.VIDEORESIZE:
                self._render_manager.screen_width = event.w
                self._render_manager.screen_height = event.h
                self._screen = self._pygame.display.set_mode((event.w, event.h), self._pygame.RESIZABLE)
                for layer_id in self._surface_dict.keys():
                    self._surface_dict[layer_id] = self._pygame.Surface((event.w, event.h), self._pygame.SRCALPHA)

                self._redraw_graph_artists()

            if self._waiting_user_input and event.type == self._pygame.KEYDOWN:
                if self._pygame.K_0 <= event.key <= self._pygame.K_9:
                    number_pressed = event.key - self._pygame.K_0
                    if number_pressed in self._input_options:
                        self._input_option_result = self._input_options[number_pressed]

    def handle_tick(self):
        self._clock.tick()
        if self._waiting_simulation:
            if self._simulation_time > self._sim_time_constant:
                self._toggle_waiting_simulation(False)
                self._simulation_time = 0
            else:
                self._simulation_time += self._clock.get_time() / 1000
                alpha = self._simulation_time / self._sim_time_constant
                alpha = self._pygame.math.clamp(alpha, 0, 1)
                for agent_artist in self._agent_artists.values():
                    agent_artist.data['_alpha'] = alpha

    def handle_single_draw(self):
        self._screen.fill(Color.White)

        # Note: Draw in layer order of back layer -> front layer
        # self._draw_grid()
        
        self._render_manager.handle_render()
        self.draw_input_overlay()
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

    def _render_text_internal(self, text: str, x: float, y: float, coord_space: Space=Space.World, color: ColorType = Color.Black):
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
        
    def _redraw_graph_artists(self):
        for artist_name, graph_artist in self._graph_artists.items():
            self.clear_layer(graph_artist.get_layer())
            self._render_manager.render_single_artist(artist_name)

    def _toggle_waiting_simulation(self, waiting_simulation: bool):
        self._waiting_simulation = waiting_simulation
        for agent_artist in self._agent_artists.values():
            agent_artist.data['_alpha'] = 0.0
            agent_artist.data['_waiting_simulation'] = waiting_simulation

    def _toggle_waiting_user_input(self, waiting_user_input: bool):
        self._waiting_user_input = waiting_user_input
        self._input_overlay_artist.data['_waiting_user_input'] = waiting_user_input
        
    def _get_target_surface(self, layer: int):
        if layer >= 0:
            return self._surface_dict.get(layer, self._screen)
        else:
            return self._screen

    def render_text(self, text: str, x: float, y: float, color: ColorType = Color.Black, perform_culling_test: bool=True):
        text_size = self._default_font.size(text)
        if perform_culling_test and self._render_manager.check_rectangle_culled(x, y, text_size[0], text_size[1]):
            return

        (x, y) = self._render_manager.world_to_screen(x, y)
        text_surface = self._default_font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        text_rect.move_ip(text_size[0] / 2, text_size[1] / 2)

        if self._render_manager.current_drawing_artist is None:
            raise ValueError("No current drawing artist set.")

        layer = self._render_manager.current_drawing_artist.get_layer()
        surface = self._get_target_surface(layer)
        surface.blit(text_surface, text_rect)

    def render_rectangle(self, x: float, y: float, width: float, height: float, color: ColorType = Color.Black,
                         perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_rectangle_culled(x, y, width, height):
            return

        (x, y) = self._render_manager.world_to_screen(x, y)

        if self._render_manager.current_drawing_artist is None:
            raise ValueError("No current drawing artist set.")

        layer = self._render_manager.current_drawing_artist.get_layer()
        surface = self._get_target_surface(layer)
        self._pygame.draw.rect(surface, color, self._pygame.Rect(x, y, width, height))

    def render_circle(self, x: float, y: float, radius: float, color: ColorType = Color.Black,
                      perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_circle_culled(x, y, radius):
            return
        
        radius = self._render_manager.world_to_screen_scale(radius)
        if radius < 1:
            return
        (x, y) = self._render_manager.world_to_screen(x, y)

        if self._render_manager.current_drawing_artist is None:
            raise ValueError("No current drawing artist set.")
        
        layer = self._render_manager.current_drawing_artist.get_layer()
        surface = self._get_target_surface(layer)
        self._pygame.draw.circle(surface, color, (x, y), radius)

    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: ColorType = Color.Black,
                    width: int=1, is_aa: bool=False, perform_culling_test: bool=True, force_no_aa: bool = False):
        if perform_culling_test and self._render_manager.check_line_culled(start_x, start_y, end_x, end_y):
            return

        (start_x, start_y) = self._render_manager.world_to_screen(start_x, start_y)
        (end_x, end_y) = self._render_manager.world_to_screen(end_x, end_y)

        if self._render_manager.current_drawing_artist is None:
            raise ValueError("No current drawing artist set.")

        layer = self._render_manager.current_drawing_artist.get_layer()
        surface = self._get_target_surface(layer)
        if is_aa:
            self._pygame.draw.aaline(surface, color, (start_x, start_y), (end_x, end_y))
        else:
            self._pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)

    def render_linestring(self, points: List[Tuple[float, float]], color: ColorType =Color.Black, width: int=1, closed: bool = False,
                     is_aa: bool=False, perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_lines_culled(points):
            return

        points = [self._render_manager.world_to_screen(point[0], point[1]) for point in points]

        if self._render_manager.current_drawing_artist is None:
            raise ValueError("No current drawing artist set.")

        layer = self._render_manager.current_drawing_artist.get_layer()
        surface = self._get_target_surface(layer)
        if is_aa:
            self._pygame.draw.aalines(surface, color, closed, points)
        else:
            self._pygame.draw.lines(surface, color, closed, points, width)

    def render_polygon(self, points: List[Tuple[float, float]], color: ColorType = Color.Black, width: int=0,
                       perform_culling_test: bool=True):
        if perform_culling_test and self._render_manager.check_polygon_culled(points):
            return

        points = [self._render_manager.world_to_screen(point[0], point[1]) for point in points]

        if self._render_manager.current_drawing_artist is None:
            raise ValueError("No current drawing artist set.")

        layer = self._render_manager.current_drawing_artist.get_layer()
        surface = self._get_target_surface(layer)
        self._pygame.draw.polygon(surface, color, points, width)

    def clear_layer(self, layer_id: int):
        if layer_id in self._surface_dict:
            self._surface_dict[layer_id].fill((0, 0, 0, 0))

    def fill_layer(self, layer_id: int, color: ColorType):
        if layer_id in self._surface_dict:
            self._surface_dict[layer_id].fill(color)

    def render_layer(self, layer_id: int):
        if layer_id in self._surface_dict:
            surface = self._surface_dict[layer_id]
            self._screen.blit(surface, (0, 0))

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
        self._pygame.display.flip()

    def human_input(self, agent_name: str, state: Dict[str, Any]) -> int:
        if self.ctx.is_terminated():
            return state["curr_pos"]
        self._toggle_waiting_user_input(True)
        def get_neighbours(state: Dict[str, Any]) -> List[int]:
            for (type, data) in state["sensor"].values():
                if type == SensorType.NEIGHBOR:
                    return data
            return []

        prev_waiting_agent_name = self._waiting_agent_name
        if prev_waiting_agent_name is not None:
            prev_waiting_agent_artist = self._agent_artists[prev_waiting_agent_name]
            prev_waiting_agent_artist.data['_is_waiting'] = False

        self._waiting_agent_name = agent_name
        waiting_agent_artist = self._agent_artists[agent_name]
        waiting_agent_artist.data['_is_waiting'] = True

        options = get_neighbours(state)

        self._input_options: dict[int, int] = {}
        for i in range(min(len(options), 10)):
            self._input_options[i] = options[i]

        self._input_overlay_artist.data['_waiting_agent_name'] = agent_name
        self._input_overlay_artist.data['_input_options'] = self._input_options

        self._input_overlay_artist.set_visible(True)
        self._redraw_graph_artists()

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
        return state["curr_pos"]

    def end_handle_human_input(self):
        for agent_artist in self._agent_artists.values():
            agent_artist.data['_is_waiting'] = False

        self._input_overlay_artist.data['_waiting_agent_name'] = None
        self._input_overlay_artist.data['_input_options'] = None

        self._input_overlay_artist.set_visible(False)
        self._toggle_waiting_user_input(False)
        self._input_option_result = None
        self._waiting_agent_name = None
        self._redraw_graph_artists()

    def simulate(self):
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.SIMULATE, data={})
        self._toggle_waiting_simulation(True)
        self._simulation_time = 0

        while self._waiting_simulation and not self._will_quit:
            self.update()

    def terminate(self):
        self._pygame.quit()
