from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import numpy as np

from gamms.osm_constants import COLOR_TYPES
from gamms.typing import (
    IVisualizationEngine,
    IArtist,
    ArtistType,
    IContext,
    SensorType,
    OpCodes,
    ColorType,
    AgentType,
)
from gamms.VisualizationEngine import Color, Shape, lazy
from gamms.VisualizationEngine.artist import Artist
from gamms.VisualizationEngine.builtin_artists import AgentData, GraphData
from gamms.VisualizationEngine.default_drawers import (
    render_agent, render_graph, render_neighbor_sensor,
    render_map_sensor, render_agent_sensor, render_input_overlay,
    render_aerial_agent_sensor, render_obstacles
)
from gamms.VisualizationEngine.render_manager import RenderManager


def _to_rgba(color: ColorType) -> Tuple[float, float, float, float]:
    vals = tuple(color)
    if len(vals) == 3:
        r, g, b = vals
        a = 255.0
    else:
        r, g, b, a = vals
    return (r / 255.0, g / 255.0, b / 255.0, a / 255.0)


class VideoBack(IVisualizationEngine):
    """Headless matplotlib visualization engine that generates frames.

    Camera, viewport, world-to-screen transforms, culling bounds and the
    artist registry are owned by a shared :class:`RenderManager`, exactly
    as in the pygame engine. Each frame runs the same artist drawer
    pipeline (``render_graph``, ``render_agent``, sensor drawers) via
    :meth:`RenderManager.handle_render`; only rasterization differs, drawn
    off-screen with the Agg backend. ``simulate`` advances one turn and
    returns the frame as an HxWx3 uint8 array. Callers own saving: files,
    video encoding and streaming live outside this engine.

    Static artists render once per camera into per-layer transparent
    bitmaps, composited in layer order under the dynamics (same
    partition the pygame engine uses for its layer caches, minus the
    display). Overlapping translucency blends; opaque art occludes by
    layer exactly as pygame paints it.
    """

    def __init__(self, ctx: IContext, width: int = 1280, height: int = 720,
                 dpi: int = 100, bgcolor: ColorType = Color.White,
                 simulation_time_constant: float = 2.0,
                 frame_rate: float = 10.0,
                 **kwargs: Dict[str, Any]) -> None:
        self.ctx = ctx
        self._width = max(1, int(width))
        self._height = max(1, int(height))
        self._dpi = max(1, int(dpi))
        self._bgcolor = _to_rgba(bgcolor)
        # Camera starts unframed (size 0): the first render centers the
        # whole graph and zooms to fill (see _render_frame). Setters
        # clamp to >= 0.1, so 0 unambiguously means 'not framed yet'.
        self._rm = RenderManager(ctx, 0, 0, 0, self._width, self._height)
        self._sim_time_constant = max(float(simulation_time_constant), 1e-6)
        self._frame_rate = max(float(frame_rate), 1e-6)
        self._simulation_time = 0.0
        self._dynamic_artists: Dict[str, IArtist] = {}
        self._dynamic_agent_artist_names: Set[str] = set()
        self._static_names: Set[str] = set()
        self._dynamic_names: Set[str] = set()
        self._seq: Dict[str, int] = {}
        self._seq_next = 0
        self._static_key: Any = None
        self._static_layers: Dict[int, Any] = {}
        self._renders = 0
        self._turn_frames: List[np.ndarray] = []
        self._terminated = False
        matplotlib = lazy('matplotlib')
        repr(matplotlib)
        matplotlib.use("Agg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import matplotlib.patches
        import matplotlib.offsetbox
        import matplotlib.image
        import importlib as _importlib
        # Backend handle for future references, mirroring
        # ``self._pygame``: every later use goes through this object,
        # so no other matplotlib import exists in the module. (pyplot
        # stays deferred to terminate: heavy import, death path only.)
        self._mpl = _importlib.import_module("matplotlib")
        self._fig = Figure(figsize=(self._width / self._dpi,
                                    self._height / self._dpi),
                           dpi=self._dpi)
        self._fig.set_canvas(FigureCanvasAgg(self._fig))
        self._fig.set_facecolor(self._bgcolor)
        self._fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
        self._ax = self._fig.add_subplot(1, 1, 1)
        _overlay_args = kwargs.get('input_overlay', {})
        _overlay_data = GraphData(node_color=_overlay_args.get('node_color', Color.Green),
                                  node_size=_overlay_args.get('node_size', 4),
                                  edge_color=_overlay_args.get('edge_color', Color.Green),
                                  draw_id=False)
        self._input_overlay_artist = Artist(self.ctx, render_input_overlay, 50)
        self._input_overlay_artist.data['_input_options'] = {}
        self._input_overlay_artist.data['_waiting_agent_name'] = None
        self._input_overlay_artist.data['_waiting_user_input'] = False
        self._input_overlay_artist.data['graph_data'] = _overlay_data
        self._input_overlay_artist.set_visible(False)
        self._input_overlay_artist.set_artist_type(ArtistType.DYNAMIC)
        self.add_artist('input_overlay', self._input_overlay_artist)



    def get_camera(self) -> Tuple[float, float, float]:
        rm = self._rm
        return (rm.camera_x, rm.camera_y, rm.camera_size)

    def set_camera(self, x: float, y: float, size: float) -> None:
        rm = self._rm
        rm.camera_x = float(x)
        rm.camera_y = float(y)
        rm.camera_size = max(float(size), 0.1)

    def pan(self, dx: float, dy: float) -> None:
        rm = self._rm
        rm.camera_x += float(dx)
        rm.camera_y += float(dy)

    def zoom(self, factor: float, center: Optional[Tuple[float, float]] = None) -> None:
        rm = self._rm
        if center is None:
            cx, cy = rm.camera_x, rm.camera_y
        else:
            cx, cy = float(center[0]), float(center[1])
        factor = float(factor)
        rm.camera_x = cx + (rm.camera_x - cx) * factor
        rm.camera_y = cy + (rm.camera_y - cy) * factor
        rm.camera_size = max(rm.camera_size * factor, 0.1)

    def zoom_to_fit(self, margin: float = 1.1) -> None:
        x_list: List[float] = []
        y_list: List[float] = []
        for node_id in self.ctx.graph.graph.get_nodes():
            node = self.ctx.graph.graph.get_node(node_id)
            x_list.append(node.x)
            y_list.append(node.y)
        if not x_list:
            return
        rm = self._rm
        rm.camera_x = (min(x_list) + max(x_list)) / 2
        rm.camera_y = (min(y_list) + max(y_list)) / 2
        # camera_size is a half-width: visible span is 2 * size (by aspect
        # in y), so fit half-spans, not full spans.
        rm.camera_size = max((max(x_list) - min(x_list)) / 2,
                             (max(y_list) - min(y_list))
                             * rm.aspect_ratio / 2, 0.0) * margin
        rm.camera_size = max(rm.camera_size, 0.1)

    def get_viewport(self) -> Optional[Tuple[float, float, float, float, float]]:
        rm = self._rm
        if rm.screen_width <= 0 or rm.screen_height <= 0 or rm.camera_size <= 0:
            self.ctx.logger.warning("Invalid viewport state")
            return None
        scale = rm.world_to_screen_scale(1.0)
        return (rm.bound_left, rm.bound_right, rm.bound_top, rm.bound_bottom, scale)

    def _z(self, frac: float, legacy: float) -> float:
        """z-order honoring artist layers (pygame paints layer by layer).

        Inside a drawer, the current artist's layer positions the
        primitive so cross-layer overlap matches pygame; direct calls
        (no current artist) keep the legacy fixed depths.
        """
        a = self._rm.current_drawing_artist
        if a is None:
            return legacy
        try:
            return float(a.get_layer()) + frac
        except Exception:
            return legacy

    def _layer_ordered(self, names: Any) -> Any:
        """Names in render order: layer, then insertion sequence.

        Matches pygame, which traverses each layer's list in insertion
        order (names only break ties across layers deterministically).
        """
        def _key(n: str) -> Any:
            a = self._rm.get_artist(n)
            layer = a.get_layer() if a is not None else 0
            return (layer, self._seq.get(n, 0))
        return sorted(names, key=_key)

    def _reset_ax(self) -> None:
        self._ax.clear()
        self._ax.set_axis_off()
        for spine in self._ax.spines.values():
            spine.set_visible(False)
        self._ax.set_facecolor(self._bgcolor)
        self._ax.set_xlim(0, self._width)
        self._ax.set_ylim(self._height, 0)
        self._ax.set_xticks([])
        self._ax.set_yticks([])

    def _render_frame(self) -> None:
        self._renders += 1
        if self._rm.camera_size <= 0.0 and self._renders % 64 == 1:
            # Default view: entire centered graph, mostly in focus.
            # Throttled: empty graphs skip the full key scan on most
            # frames, late-attached graphs still frame within 64.
            self.zoom_to_fit()
        if self._rm.camera_size <= 0.0:
            # Nothing mappable: draw the blank frame without running
            # artists (custom drawers calling world_to_screen directly
            # would divide by zero on a zero-size camera).
            self._fig.canvas.draw()
            return
        # Reconcile partition sets with live artist types (catches
        # post-add set_artist_type() flips, which neither engine tracks).
        _part_changed = False
        for _n in list(self._static_names | self._dynamic_names):
            _a = self._rm.get_artist(_n)
            if _a is None:
                if _n in self._static_names or _n in self._dynamic_names:
                    _part_changed = True
                self._static_names.discard(_n)
                self._dynamic_names.discard(_n)
                self._dynamic_artists.pop(_n, None)
                self._dynamic_agent_artist_names.discard(_n)
                self._seq.pop(_n, None)
                continue
            _want_static = _a.get_artist_type() == ArtistType.STATIC
            if _want_static == (_n in self._static_names):
                continue
            _part_changed = True
            if _want_static:
                self._static_names.add(_n)
                self._dynamic_names.discard(_n)
                self._dynamic_artists.pop(_n, None)
                self._dynamic_agent_artist_names.discard(_n)
            else:
                self._dynamic_names.add(_n)
                self._static_names.discard(_n)
                self._dynamic_artists[_n] = _a
                if "agent_data" in _a.data:
                    self._dynamic_agent_artist_names.add(_n)
                else:
                    self._dynamic_agent_artist_names.discard(_n)
        if _part_changed:
            self._static_key = None
        rm = self._rm
        # Cache key: camera + static names, layers, visibility. Artist
        # *data* mutation is not tracked (same blindness as pygame's
        # name-keyed cache): re-add the artist to invalidate.
        _sst = []
        for _n in sorted(self._static_names):
            _a = self._rm.get_artist(_n)
            _sst.append((_n, _a.get_layer() if _a is not None else 0,
                         bool(_a is not None and _a.get_visible())))
        key = (round(rm.camera_x, 3), round(rm.camera_y, 3),
               round(rm.camera_size, 6), self._width, self._height,
               tuple(_sst))
        if key != self._static_key:
            # Draw each static layer to its own transparent bitmap.
            # Transparent so layers composite in order (a static layer
            # above a dynamic one draws above it, as in pygame); the
            # figure/axes facecolor underneath supplies the background.
            _by_layer: Dict[int, Any] = {}
            for _n in self._static_names:
                _a = self._rm.get_artist(_n)
                if _a is not None and _a.get_visible():
                    _by_layer.setdefault(_a.get_layer(), []).append(_n)
            # Transparent figure during capture: Agg composites over the
            # opaque figure patch otherwise, baking alpha=255 everywhere
            # and letting upper layers bury lower ones. Restored after.
            _fig_patch = self._fig.patch
            _old_alpha = _fig_patch.get_alpha()
            _fig_patch.set_alpha(0.0)
            try:
                self._static_layers = {}
                for _layer in sorted(_by_layer):
                    self._reset_ax()
                    self._ax.set_facecolor((0, 0, 0, 0))
                    for _n in self._layer_ordered(_by_layer[_layer]):
                        _a = self._rm.get_artist(_n)
                        if _a is not None and _a.get_visible():
                            self._rm.render_single_artist(_n)
                    self._fig.canvas.draw()
                    _buf = np.asarray(self._fig.canvas.buffer_rgba())
                    self._static_layers[_layer] = _buf.copy()
            finally:
                _fig_patch.set_alpha(_old_alpha)
            self._static_key = key
        _dyn: Dict[int, Any] = {}
        for _n in self._dynamic_names:
            _a = self._rm.get_artist(_n)
            if _a is not None and _a.get_visible():
                _dyn.setdefault(_a.get_layer(), []).append(_n)
        self._reset_ax()
        for _layer in sorted(set(self._static_layers) | set(_dyn)):
            if _layer in self._static_layers:
                self._ax.imshow(self._static_layers[_layer],
                                extent=(0, self._width,
                                        self._height, 0),
                                zorder=float(_layer), interpolation="nearest",
                                aspect="auto")
            for _n in self._layer_ordered(_dyn.get(_layer, [])):
                self._rm.render_single_artist(_n)
        self._fig.canvas.draw()

    def handle_tick(self, dt: float) -> None:
        self._simulation_time += dt
        alpha = self._simulation_time / self._sim_time_constant
        alpha = min(max(alpha, 0.0), 1.0)
        for artist in self._dynamic_artists.values():
            artist.data['_alpha'] = alpha

    def simulate(self) -> Optional[np.ndarray]:
        if self.ctx.record.record():
            self.ctx.record.write(opCode=OpCodes.SIMULATE, data={})
        self._toggle_waiting_simulation(True)
        self._simulation_time = 0.0
        self._turn_frames = []
        dt = 1.0 / self._frame_rate
        steps = max(1, int(round(self._sim_time_constant * self._frame_rate)))
        for _ in range(steps):
            self.handle_tick(dt)
            self._render_frame()
            buf = np.asarray(self._fig.canvas.buffer_rgba())
            self._turn_frames.append(buf[:, :, :3].copy())
        self._toggle_waiting_simulation(False)
        return self._turn_frames[-1]

    @property
    def turn_frames(self) -> List[np.ndarray]:
        """Frames rendered for the current turn (interpolated animation)."""
        return self._turn_frames

    def pop_turn_frames(self) -> List[np.ndarray]:
        """Take the current turn's frames, clearing the buffer."""
        frames, self._turn_frames = self._turn_frames, []
        return frames

    def human_input(self, agent_name: str, state: Dict[str, Any]) -> Union[int, Tuple[float, float, float]]:
        agent = self.ctx.agent.get_agent(agent_name)
        if agent.type == AgentType.BASIC:
            return state["curr_pos"]
        elif agent.type == AgentType.AERIAL:
            return (0.0, 0.0, 0.0)
        else:
            raise RuntimeError(f"Unknown agent type {agent.type} for agent {agent_name}")

    def terminate(self) -> None:
        if self._terminated:
            return
        self._terminated = True
        try:
            import matplotlib.pyplot as plt
            plt.close(self._fig)
        except Exception:
            pass

    def set_graph_visual(self, **kwargs: Dict[str, Any]) -> IArtist:
        # Deliberately not pygame's set_origin block: it frames at twice the
        # needed size (full spans into a half-width) and int-truncates the
        # center. VideoBack frames tight via zoom_to_fit instead.
        self.zoom_to_fit()

        graph_data = GraphData(node_color=cast(ColorType, kwargs.get('node_color', Color.DarkGray)),
                               node_size=cast(int, kwargs.get('node_size', 2)),
                               edge_color=cast(ColorType, kwargs.get('edge_color', Color.LightGray)),
                               draw_id=cast(bool, kwargs.get('draw_id', False)))

        artist = Artist(self.ctx, render_graph, 10)
        artist.data['graph_data'] = graph_data
        artist.set_artist_type(ArtistType.STATIC)

        self.add_artist('graph', artist)

        return artist

    def set_obstacle_visual(self, **kwargs: Dict[str, Any]) -> IArtist:
        boundary_thickness = cast(float, kwargs.get('boundary_thickness', 1.0))
        color_code = cast(Dict[int, ColorType], {k: tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) for k, color in COLOR_TYPES.items()})
        color_code.update(
            cast(Dict[int, ColorType], kwargs.get('color_map', {}))
        )

        artist = Artist(self.ctx, render_obstacles, 5)
        artist.data['boundary_thickness'] = boundary_thickness
        artist.data['color_map'] = color_code
        artist.set_artist_type(ArtistType.STATIC)

        self.add_artist('obstacles', artist)

        return artist

    def set_agent_visual(self, name: str, **kwargs: Dict[str, Any]) -> IArtist:
        agent_data = AgentData(
            name=name,
            color=cast(ColorType, kwargs.get('color', Color.Black)),
            size=cast(int, kwargs.get('size', 8))
        )
        _image_path = kwargs.get('image_path')
        if _image_path is None:
            agent_data.image = None
        else:
            _image_file = Path(str(_image_path))
            if not _image_file.exists():
                raise FileNotFoundError(f"Agent image not found: {_image_file}")
            agent_data.image = self._mpl.image.imread(str(_image_file))

        artist = Artist(self.ctx, render_agent, 20)
        artist.data['agent_data'] = agent_data
        artist.set_artist_type(ArtistType.DYNAMIC)
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
        elif sensor_type in (SensorType.MAP, SensorType.RANGE, SensorType.ARC, SensorType.AERIAL,
                             SensorType.OCCLUDED_MAP, SensorType.OCCLUDED_AERIAL):
            drawer = render_map_sensor
            data['node_color'] = kwargs.pop('node_color', Color.Cyan)
            data['edge_color'] = kwargs.pop('edge_color', Color.Cyan)
        elif sensor_type in (SensorType.AGENT, SensorType.AGENT_RANGE, SensorType.AGENT_ARC,
                             SensorType.OCCLUDED_AGENT):
            drawer = render_agent_sensor
            data['color'] = kwargs.pop('color', Color.Cyan)
            data['size'] = kwargs.pop('size', 8)
        elif sensor_type in (SensorType.AERIAL_AGENT, SensorType.OCCLUDED_AERIAL_AGENT):
            drawer = render_aerial_agent_sensor
            data['color'] = kwargs.pop('color', Color.Cyan)
            data['size'] = kwargs.pop('size', 8)
        else:
            raise ValueError(f"Invalid sensor type: {sensor_type}")

        layer = cast(int, kwargs.pop('layer', 30))
        artist = Artist(self.ctx, drawer, layer)
        artist.data.update(data)
        artist.set_artist_type(ArtistType.DYNAMIC)

        self.add_artist(f'sensor_{name}', artist)

        return artist

    def add_artist(self, name: str, artist: Union[IArtist, Dict[str, Any]]) -> IArtist:
        """Register an artist. All registration must go through here:
        artists added directly to the render manager are invisible to
        the partition sets and will never draw."""
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

        if self._rm.get_artist(name) is not None:
            self._rm.remove_artist(name)
        self._rm.add_artist(name, artist_to_add)
        self._seq[name] = self._seq_next
        self._seq_next += 1
        if artist_to_add.get_artist_type() == ArtistType.STATIC:
            self._dynamic_artists.pop(name, None)
            self._dynamic_agent_artist_names.discard(name)
            self._static_names.add(name)
            self._dynamic_names.discard(name)
            self._static_key = None
        elif artist_to_add.get_artist_type() == ArtistType.DYNAMIC:
            self._static_names.discard(name)
            self._dynamic_names.add(name)
            self._dynamic_artists[name] = artist_to_add
            if 'agent_data' in artist_to_add.data:
                self._dynamic_agent_artist_names.add(name)
            else:
                self._dynamic_agent_artist_names.discard(name)
        return artist_to_add

    def remove_artist(self, name: str) -> None:
        if self._rm.get_artist(name) is not None:
            self._rm.remove_artist(name)
        self._dynamic_artists.pop(name, None)
        self._dynamic_agent_artist_names.discard(name)
        self._static_names.discard(name)
        self._dynamic_names.discard(name)
        self._seq.pop(name, None)
        self._static_key = None

    def _toggle_waiting_simulation(self, waiting_simulation: bool) -> None:
        _stale_names: List[str] = []
        for _name in self._dynamic_agent_artist_names:
            _agent_artist = self._dynamic_artists.get(_name)
            if _agent_artist is None or 'agent_data' not in _agent_artist.data:
                _stale_names.append(_name)
                continue
            _agent_artist.data['_waiting_simulation'] = waiting_simulation
        for _name in _stale_names:
            self._dynamic_agent_artist_names.discard(_name)
        for artist in self._dynamic_artists.values():
            artist.data['_alpha'] = 0.0

    def render_circle(self, x: float, y: float, radius: float,
                      color: ColorType = Color.Black, width: int = 0,
                      perform_culling_test: bool = True) -> None:
        if perform_culling_test and self._rm.check_circle_culled(x, y, radius):
            return
        radius = self._rm.world_to_screen_scale(radius)
        if radius < 1:
            return
        sx, sy = self._rm.world_to_screen(x, y)
        rgba = _to_rgba(color)
        if width == 0:
            artist = self._mpl.patches.Circle((sx, sy), radius, facecolor=rgba,
                            edgecolor=None, linewidth=0, zorder=self._z(0.4, 4.0))
        else:
            artist = self._mpl.patches.Circle((sx, sy), radius, facecolor=(0, 0, 0, 0),
                            edgecolor=rgba,
                            linewidth=width * 72.0 / self._dpi, zorder=self._z(0.4, 4.0))
        self._ax.add_patch(artist)

    def render_rectangle(self, x: float, y: float, width: float, height: float,
                         color: ColorType = Color.Black, perform_culling_test: bool = True) -> None:
        if perform_culling_test and self._rm.check_rectangle_culled(x, y, width, height):
            return
        sx, sy = self._rm.world_to_screen(x, y)
        scale = self._rm.world_to_screen_scale(1.0)
        artist = self._mpl.patches.Rectangle((sx - width * scale / 2, sy - height * scale / 2),
                           width * scale, height * scale,
                           facecolor=_to_rgba(color), edgecolor=None,
                           linewidth=0, zorder=self._z(0.4, 4.0))
        self._ax.add_patch(artist)

    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float,
                    color: ColorType = Color.Black, width: int = 1, is_aa: bool = False,
                    perform_culling_test: bool = True) -> None:
        if perform_culling_test and self._rm.check_line_culled(start_x, start_y, end_x, end_y):
            return
        x0, y0 = self._rm.world_to_screen(start_x, start_y)
        x1, y1 = self._rm.world_to_screen(end_x, end_y)
        self._ax.plot([x0, x1], [y0, y1], color=_to_rgba(color),
                      linewidth=width * 72.0 / self._dpi,
                      zorder=self._z(0.4, 4.0))

    def render_linestring(self, points: List[Tuple[float, float]],
                          color: ColorType = Color.Black, width: int = 1,
                          closed: bool = False, is_aa: bool = False,
                          perform_culling_test: bool = True) -> None:
        if perform_culling_test and self._rm.check_lines_culled(points):
            return
        pts = [self._rm.world_to_screen(x, y) for x, y in points]
        if closed and pts:
            pts = pts + pts[:1]
        if pts:
            xs, ys = zip(*pts)
            self._ax.plot(list(xs), list(ys), color=_to_rgba(color),
                          linewidth=width * 72.0 / self._dpi,
                          zorder=self._z(0.4, 4.0))

    def render_polygon(self, points: List[Tuple[float, float]],
                       color: ColorType = Color.Black, width: int = 0,
                       perform_culling_test: bool = True) -> None:
        if perform_culling_test and self._rm.check_polygon_culled(points):
            return
        pts = [self._rm.world_to_screen(x, y) for x, y in points]
        if not pts:
            return
        rgba = _to_rgba(color)
        if width == 0:
            artist = self._mpl.patches.Polygon(pts, closed=True, facecolor=rgba, edgecolor=None,
                             linewidth=0, zorder=self._z(0.4, 4.0))
        else:
            artist = self._mpl.patches.Polygon(pts, closed=True, facecolor=(0, 0, 0, 0),
                             edgecolor=rgba,
                             linewidth=width * 72.0 / self._dpi, zorder=self._z(0.4, 4.0))
        self._ax.add_patch(artist)

    def render_text(self, text: str, x: float, y: float,
                    color: ColorType = Color.Black, perform_culling_test: bool = True,
                    font_size: Optional[int] = None) -> None:
        if perform_culling_test and self._rm.check_rectangle_culled(
                x, y, 1.0, 1.0):
            return
        sx, sy = self._rm.world_to_screen(x, y)
        self._ax.text(sx, sy, str(text), fontsize=font_size or 36,
                      color=_to_rgba(color), ha="center", va="center",
                      zorder=self._z(0.6, 6.0))

    def render_image(self, x: float, y: float, image: Any, size: float,
                     angle: float = 0.0, perform_culling_test: bool = True) -> None:
        if image is None:
            return

        diameter = size * 2
        if perform_culling_test and self._rm.check_rectangle_culled(x, y, diameter, diameter):
            return
        sx, sy = self._rm.world_to_screen(x, y)
        scale = self._rm.world_to_screen_scale(1.0)
        box = self._mpl.offsetbox.OffsetImage(image, zoom=size * scale / 72.0)
        self._ax.add_artist(self._mpl.offsetbox.AnnotationBbox(box, (sx, sy), frameon=False,
                                           zorder=self._z(0.4, 4.0)))

    def render_layer(self, layer_id: int) -> None:
        self._render_frame()
