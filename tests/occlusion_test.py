"""
Occlusion sensor tests.

"""

import math
import unittest

import numpy as np

import gamms
import gamms.typing
import gamms.typing.agent_engine
from gamms.SensorEngine.sensors_occluded import (
    _quad_blocks,
    _quad_blocks_batch,
    _segment_triangle,
)


# ---------------------------------------------------------------------------
# Grid / building helpers shared by all test classes
# ---------------------------------------------------------------------------

_GRID_N       = 5
_GRID_SPACING = 10.0    # metres between adjacent nodes
_WALL_HEIGHT  = 8.0     # metres — tall enough to block eye-level rays

_face_id_counter = 0    # module-level counter so IDs never collide across tests


def _next_face_ids(n: int):
    global _face_id_counter
    start = _face_id_counter
    _face_id_counter += n
    return range(start, start + n)


def _box_faces(x0: float, y0: float, x1: float, y1: float, height: float):
    """4 ObsFace dicts for a closed rectangular building footprint."""
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    ids = _next_face_ids(4)
    faces = []
    for i, fid in enumerate(ids):
        p1, p2 = corners[i], corners[(i + 1) % 4]
        faces.append({
            'id':  fid,
            'tl': (p1[0], p1[1], height),
            'tr': (p2[0], p2[1], height),
            'br': (p2[0], p2[1], 0.0),
            'bl': (p1[0], p1[1], 0.0),
        })
    return faces


# ---------------------------------------------------------------------------
# Geometry stubs (for unit tests that don't need the full context)
# ---------------------------------------------------------------------------

class _Face:
    __slots__ = ('tl', 'tr', 'br', 'bl')

    def __init__(self, tl, tr, br, bl):
        self.tl = tl; self.tr = tr; self.br = br; self.bl = bl


# 1 m × 2 m wall at x=5, y ∈ [-0.5, 0.5], z ∈ [0, 2]
_UNIT_WALL = _Face(
    tl=(5.0, -0.5, 2.0), tr=(5.0, 0.5, 2.0),
    br=(5.0,  0.5, 0.0), bl=(5.0, -0.5, 0.0),
)


# ---------------------------------------------------------------------------
# Base class: 5 × 5 grid context
# ---------------------------------------------------------------------------

class GridTest(unittest.TestCase):
    """Sets up a 5×5 node grid and tears it down after each test."""

    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={'level': 'CRITICAL'},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        self._build_grid()

    def tearDown(self):
        self.ctx.terminate()

    # ---- grid construction ------------------------------------------------

    def _build_grid(self):
        g = gamms.create_context   # just to satisfy linter, we use self.ctx below
        g = self.ctx.graph.graph
        N, S = _GRID_N, _GRID_SPACING
        for row in range(N):
            for col in range(N):
                g.add_node({'id': self.nid(row, col),
                             'x': col * S, 'y': row * S})
        eid = 0
        for row in range(N):
            for col in range(N):
                src = self.nid(row, col)
                if col + 1 < N:
                    g.add_edge({'id': eid, 'source': src,
                                 'target': self.nid(row, col + 1),
                                 'length': S})
                    eid += 1
                if row + 1 < N:
                    g.add_edge({'id': eid, 'source': src,
                                 'target': self.nid(row + 1, col),
                                 'length': S})
                    eid += 1

    def nid(self, row: int, col: int) -> int:
        return row * _GRID_N + col

    def pos(self, row: int, col: int):
        return col * _GRID_SPACING, row * _GRID_SPACING

    # ---- building helpers -------------------------------------------------

    def add_building(self, x0, y0, x1, y1, height=_WALL_HEIGHT):
        for f in _box_faces(x0, y0, x1, y1, height):
            self.ctx.graph.add_obstacle_face(
                f['id'], tl=f['tl'], tr=f['tr'], br=f['br'], bl=f['bl'], type=0,
            )

    def add_building_between(self, row0, col0, row1, col1,
                              thickness=2.0, height=_WALL_HEIGHT):
        """Place a building slab on the midpoint of the edge (row0,col0)→(row1,col1)."""
        x0, y0 = self.pos(row0, col0)
        x1, y1 = self.pos(row1, col1)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if row0 == row1:   # horizontal edge — wall perpendicular to x-axis
            self.add_building(mx - 1, my - thickness, mx + 1, my + thickness, height)
        else:              # vertical edge — wall perpendicular to y-axis
            self.add_building(mx - thickness, my - 1, mx + thickness, my + 1, height)

    # ---- sensor helpers ---------------------------------------------------

    def make_sensor(self, label, sensor_type, **kwargs):
        return self.ctx.sensor.create_sensor(label, sensor_type, **kwargs)

    def occluded_map(self, label='occ', **kwargs):
        return self.make_sensor(label, gamms.typing.SensorType.OCCLUDED_MAP, **kwargs)

    def occluded_agent(self, label='occ_agent', **kwargs):
        return self.make_sensor(label, gamms.typing.SensorType.OCCLUDED_AGENT, **kwargs)

    def occluded_aerial(self, label='occ_aerial', **kwargs):
        return self.make_sensor(label, gamms.typing.SensorType.OCCLUDED_AERIAL, **kwargs)

    def occluded_aerial_agent(self, label='occ_aerial_agent', **kwargs):
        return self.make_sensor(label, gamms.typing.SensorType.OCCLUDED_AERIAL_AGENT, **kwargs)


# ---------------------------------------------------------------------------
# Scalar Möller-Trumbore unit tests
# ---------------------------------------------------------------------------

class SegmentTriangleTest(unittest.TestCase):
    """Triangle at x=5: v0=(5,-1,0), v1=(5,1,0), v2=(5,0,2)."""

    V0 = (5.0, -1.0, 0.0)
    V1 = (5.0,  1.0, 0.0)
    V2 = (5.0,  0.0, 2.0)

    def hit(self, a, b):
        return _segment_triangle(a, b, self.V0, self.V1, self.V2)

    def test_centre_hit(self):
        self.assertTrue(self.hit((0, 0, 0.67), (10, 0, 0.67)))

    def test_near_apex(self):
        self.assertTrue(self.hit((0, 0, 1.9), (10, 0, 1.9)))

    def test_near_base_left(self):
        self.assertTrue(self.hit((0, -0.9, 0.05), (10, -0.9, 0.05)))

    def test_miss_above_apex(self):
        self.assertFalse(self.hit((0, 0, 2.1), (10, 0, 2.1)))

    def test_miss_below_base(self):
        self.assertFalse(self.hit((0, 0, -0.1), (10, 0, -0.1)))

    def test_miss_left_of_triangle(self):
        self.assertFalse(self.hit((0, -1.1, 0.5), (10, -1.1, 0.5)))

    def test_miss_right_of_triangle(self):
        self.assertFalse(self.hit((0, 1.1, 0.5), (10, 1.1, 0.5)))

    def test_segment_stops_before_plane(self):
        self.assertFalse(self.hit((0, 0, 0.67), (4.99, 0, 0.67)))

    def test_segment_endpoint_on_triangle(self):
        self.assertTrue(self.hit((0, 0, 0.67), (5, 0, 0.67)))

    def test_segment_starts_past_triangle(self):
        self.assertFalse(self.hit((6, 0, 0.67), (10, 0, 0.67)))

    def test_parallel_to_plane(self):
        self.assertFalse(self.hit((0, 0, 1), (0, 10, 1)))

    def test_zero_length_segment(self):
        self.assertFalse(self.hit((5, 0, 0.67), (5, 0, 0.67)))

    def test_ray_in_triangle_plane(self):
        self.assertFalse(self.hit((5, -0.5, 0.5), (5, 0.5, 0.5)))

    def test_reversed_direction_still_hits(self):
        self.assertTrue(self.hit((10, 0, 0.67), (0, 0, 0.67)))

    def test_origin_on_triangle(self):
        self.assertTrue(self.hit((5, 0, 0.67), (10, 0, 0.67)))


# ---------------------------------------------------------------------------
# Scalar quad blocks unit tests
# ---------------------------------------------------------------------------

class QuadBlocksTest(unittest.TestCase):

    def test_ray_hits_wall(self):
        self.assertTrue(_quad_blocks((0, 0, 1), (10, 0, 1), _UNIT_WALL))

    def test_angled_ray_hits(self):
        self.assertTrue(_quad_blocks((0, -0.4, 0.5), (10, 0.4, 1.5), _UNIT_WALL))

    def test_hit_lower_triangle(self):
        self.assertTrue(_quad_blocks((0, -0.4, 0.1), (10, -0.4, 0.1), _UNIT_WALL))

    def test_hit_upper_triangle(self):
        self.assertTrue(_quad_blocks((0, 0.4, 1.8), (10, 0.4, 1.8), _UNIT_WALL))

    def test_miss_wide_left(self):
        self.assertFalse(_quad_blocks((0, -2, 1), (10, -2, 1), _UNIT_WALL))

    def test_miss_wide_right(self):
        self.assertFalse(_quad_blocks((0, 2, 1), (10, 2, 1), _UNIT_WALL))

    def test_miss_above_wall(self):
        self.assertFalse(_quad_blocks((0, 0, 2.5), (10, 0, 2.5), _UNIT_WALL))

    def test_miss_below_wall(self):
        self.assertFalse(_quad_blocks((0, 0, -0.5), (10, 0, -0.5), _UNIT_WALL))

    def test_segment_stops_before_wall(self):
        self.assertFalse(_quad_blocks((0, 0, 1), (4.9, 0, 1), _UNIT_WALL))

    def test_both_endpoints_behind_wall(self):
        self.assertFalse(_quad_blocks((6, 0, 1), (9, 0, 1), _UNIT_WALL))

    def test_observer_behind_wall(self):
        self.assertFalse(_quad_blocks((7, 0, 1), (12, 0, 1), _UNIT_WALL))

    def test_diagonal_wall_hit(self):
        diag = _Face(
            tl=(3.0, 3.0, 4.0), tr=(7.0, 7.0, 4.0),
            br=(7.0, 7.0, 0.0), bl=(3.0, 3.0, 0.0),
        )
        self.assertTrue(_quad_blocks((0, 5, 2), (10, 5, 2), diag))

    def test_diagonal_wall_parallel_miss(self):
        diag = _Face(
            tl=(3.0, 3.0, 4.0), tr=(7.0, 7.0, 4.0),
            br=(7.0, 7.0, 0.0), bl=(3.0, 3.0, 0.0),
        )
        self.assertFalse(_quad_blocks((0, 8, 2), (10, 8, 2), diag))


# ---------------------------------------------------------------------------
# Vectorised batch unit tests
# ---------------------------------------------------------------------------

class QuadBlocksBatchTest(unittest.TestCase):

    OBS = np.array([0.0, 0.0, 1.0])

    def test_empty_returns_empty_bool_array(self):
        result = _quad_blocks_batch(self.OBS, np.zeros((0, 3)), _UNIT_WALL)
        self.assertEqual(len(result), 0)
        self.assertEqual(result.dtype, bool)

    def test_single_blocked(self):
        self.assertTrue(_quad_blocks_batch(self.OBS, np.array([[10.0, 0.0, 1.0]]), _UNIT_WALL)[0])

    def test_single_clear(self):
        self.assertFalse(_quad_blocks_batch(self.OBS, np.array([[10.0, 5.0, 1.0]]), _UNIT_WALL)[0])

    def test_all_blocked(self):
        targets = np.array([[10.0, 0.0, 0.5], [12.0, 0.0, 1.0], [15.0, 0.2, 1.5]])
        self.assertTrue(_quad_blocks_batch(self.OBS, targets, _UNIT_WALL).all())

    def test_none_blocked(self):
        targets = np.array([
            [10.0,  5.0, 1.0],   # beside
            [10.0, -5.0, 1.0],   # beside
            [ 3.0,  0.0, 1.0],   # in front of wall
            [10.0,  0.0, 5.0],   # above (z=5 clears top at z=2)
        ])
        self.assertFalse(_quad_blocks_batch(self.OBS, targets, _UNIT_WALL).any())

    def test_mixed(self):
        targets = np.array([
            [10.0,  0.0, 1.0],   # blocked
            [10.0,  5.0, 1.0],   # clear — beside
            [10.0,  0.0, 5.0],   # clear — above
            [10.0, -0.4, 0.2],   # blocked — lower triangle
            [ 3.0,  0.0, 1.0],   # clear — in front
        ])
        self.assertEqual(list(_quad_blocks_batch(self.OBS, targets, _UNIT_WALL)),
                         [True, False, False, True, False])

    def test_large_batch_matches_scalar(self):
        rng = np.random.default_rng(0)
        targets = rng.uniform(low=[6, -3, 0], high=[15, 3, 4], size=(300, 3))
        batch = _quad_blocks_batch(self.OBS, targets, _UNIT_WALL)
        for i, t in enumerate(targets):
            self.assertEqual(bool(batch[i]),
                             _quad_blocks(tuple(self.OBS), tuple(t), _UNIT_WALL),  # type: ignore[arg-type]
                             msg=f"mismatch at target {i}: {t}")


# ---------------------------------------------------------------------------
# Map sensor — grid scenarios
# ---------------------------------------------------------------------------

class OccludedMapSensorTest(GridTest):
    """
    Observer always at node (0,0) = position (0,0).
    Sensor range 25 m covers rows 0–2 and cols 0–2 with no FOV restriction.
    """

    RANGE = 25.0

    def _sense(self, label='occ'):
        s = self.occluded_map(label, sensor_range=self.RANGE)
        s.sense(self.nid(0, 0))
        return s.data

    def test_no_building_all_nodes_visible(self):
        data = self._sense()
        # Nodes within 25 m of (0,0): rows/cols 0–2 except the (2,2) corner
        # which sits at distance √800 ≈ 28.3 m (outside range).
        import math
        for row in range(3):
            for col in range(3):
                dist = math.hypot(col * _GRID_SPACING, row * _GRID_SPACING)
                if dist > self.RANGE:
                    continue  # genuinely out of sensor range — skip
                self.assertIn(self.nid(row, col), data['nodes'],
                              msg=f"node ({row},{col}) missing with no buildings")

    def test_building_blocks_column_ahead(self):
        # Wall slab at x=5 (between col 0 and col 1), centred on y=0 axis.
        # Blocks all nodes with col >= 1 and row == 0 when looking straight along +x.
        self.add_building(4, -3, 6, 3)
        data = self._sense()
        self.assertIn(self.nid(0, 0), data['nodes'])          # observer always visible
        self.assertNotIn(self.nid(0, 1), data['nodes'])       # directly behind wall
        self.assertNotIn(self.nid(0, 2), data['nodes'])       # further behind wall

    def test_building_does_not_block_perpendicular_nodes(self):
        # Same wall along x=5 — nodes above (col 0, row 1+) have clear LOS.
        self.add_building(4, -3, 6, 3)
        data = self._sense()
        self.assertIn(self.nid(1, 0), data['nodes'])
        self.assertIn(self.nid(2, 0), data['nodes'])

    def test_building_beside_path_does_not_occlude(self):
        # Building far off to the side (y > 15) — no ray to any in-range node crosses it.
        self.add_building(3, 18, 7, 22)
        data = self._sense()
        for col in range(3):
            self.assertIn(self.nid(0, col), data['nodes'],
                          msg=f"node (0,{col}) should be visible past a side building")

    def test_two_buildings_each_block_one_direction(self):
        # Building A: blocks +x from origin (between col 0 and col 1).
        self.add_building(4, -3, 6, 3)
        # Building B: blocks +y from origin (between row 0 and row 1).
        self.add_building(-3, 4, 3, 6)
        data = self._sense()
        self.assertIn(self.nid(0, 0), data['nodes'])
        self.assertNotIn(self.nid(0, 1), data['nodes'])   # blocked by A
        self.assertNotIn(self.nid(1, 0), data['nodes'])   # blocked by B

    def test_observer_node_always_in_output(self):
        self.add_building(4, -3, 6, 3)
        data = self._sense()
        self.assertIn(self.nid(0, 0), data['nodes'])

    def test_edge_excluded_when_both_endpoints_hidden(self):
        self.add_building(4, -3, 6, 3)
        data = self._sense()
        visible = set(data['nodes'].keys())
        for edge in data['edges']:
            self.assertIn(edge.source, visible)
            self.assertIn(edge.target, visible)

    def test_building_outside_range_not_loaded(self):
        # Building at x=100 is far outside the 25 m sensor range — must be ignored.
        self.add_building(99, -3, 101, 3)
        data = self._sense()
        # Nodes in col 1 and 2 should still be visible (no occluder in range).
        self.assertIn(self.nid(0, 1), data['nodes'])
        self.assertIn(self.nid(0, 2), data['nodes'])

    def test_tall_building_blocks_low_observer(self):
        # 8 m wall easily blocks a 1.6 m observer.
        self.add_building(4, -3, 6, 3, height=_WALL_HEIGHT)
        data = self._sense()
        self.assertNotIn(self.nid(0, 1), data['nodes'])

    def test_short_building_does_not_block_observer(self):
        # A 1 m wall is shorter than the observer eye-level (1.6 m) — ray passes over.
        self.add_building(4, -3, 6, 3, height=1.0)
        data = self._sense()
        self.assertIn(self.nid(0, 1), data['nodes'])

    def test_infinite_range_still_occludes(self):
        self.add_building(4, -3, 6, 3)
        s = self.occluded_map('occ_inf', sensor_range=float('inf'))
        s.sense(self.nid(0, 0))
        self.assertNotIn(self.nid(0, 1), s.data['nodes'])

    def test_infinite_range_far_nodes_visible(self):
        # No buildings — all 25 nodes reachable with infinite range.
        s = self.occluded_map('occ_inf', sensor_range=float('inf'))
        s.sense(self.nid(0, 0))
        self.assertEqual(len(s.data['nodes']), _GRID_N ** 2)


# ---------------------------------------------------------------------------
# Map sensor — FOV scenarios
# ---------------------------------------------------------------------------

class OccludedMapFovTest(GridTest):
    """
    FOV and occlusion compose: observer at (0,0), orientation=(1,0) (+x).
    FOV = π/2 (90°) → ±45° half-cone.

    Nodes in the +x direction (row 0, col 1+) are inside the cone.
    Nodes in the +y direction (row 1+, col 0) are outside the cone.
    """

    def _sense_fov(self, fov, label='occ_fov', **kwargs):
        s = self.occluded_map(label, sensor_range=25.0, fov=fov,
                               orientation=(1.0, 0.0), **kwargs)
        s.sense(self.nid(0, 0))
        return s.data

    def test_forward_node_inside_cone(self):
        data = self._sense_fov(math.pi / 2)
        self.assertIn(self.nid(0, 1), data['nodes'])

    def test_perpendicular_node_outside_cone(self):
        # Node directly above (row 1, col 0) is at 90° — outside ±45° cone.
        data = self._sense_fov(math.pi / 2)
        self.assertNotIn(self.nid(1, 0), data['nodes'])

    def test_wall_blocks_forward_node_inside_cone(self):
        self.add_building(4, -3, 6, 3)
        data = self._sense_fov(math.pi / 2)
        self.assertNotIn(self.nid(0, 1), data['nodes'])   # wall occludes

    def test_full_fov_ignores_cone_keeps_wall(self):
        # 2π FOV — cone is off; only the wall matters.
        self.add_building(4, -3, 6, 3)
        data = self._sense_fov(2 * math.pi)
        self.assertNotIn(self.nid(0, 1), data['nodes'])   # wall
        self.assertIn(self.nid(1, 0), data['nodes'])      # clear LOS, was outside cone

    def test_narrow_fov_cuts_diagonal_node(self):
        # Node (1,1) is at 45° — right on the edge for fov=π/2 (half-angle 45°).
        # fov=π/3 (60°, half-angle 30°) should cut it.
        data = self._sense_fov(math.pi / 3)
        self.assertNotIn(self.nid(1, 1), data['nodes'])


# ---------------------------------------------------------------------------
# Agent sensor — grid scenarios
# ---------------------------------------------------------------------------

class OccludedAgentSensorTest(GridTest):
    """Observer at node (0,0); agents placed at various grid nodes."""

    def _add_agent(self, name, row, col):
        self.ctx.agent.create_agent(name, start_node_id=self.nid(row, col))

    def test_no_building_all_agents_visible(self):
        self._add_agent('a1', 0, 1)
        self._add_agent('a2', 1, 0)
        s = self.occluded_agent(sensor_range=25.0)
        s.sense(self.nid(0, 0))
        self.assertIn('a1', s.data)
        self.assertIn('a2', s.data)

    def test_building_hides_agent_behind_it(self):
        self.add_building(4, -3, 6, 3)
        self._add_agent('hidden', 0, 1)
        self._add_agent('visible', 1, 0)
        s = self.occluded_agent(sensor_range=25.0)
        s.sense(self.nid(0, 0))
        self.assertNotIn('hidden', s.data)
        self.assertIn('visible', s.data)

    def test_agent_at_same_node_as_observer_visible(self):
        self._add_agent('same_spot', 0, 0)
        s = self.occluded_agent(sensor_range=25.0)
        s.sense(self.nid(0, 0))
        self.assertIn('same_spot', s.data)

    def test_two_buildings_each_hide_one_agent(self):
        self.add_building(4, -3, 6, 3)         # blocks +x
        self.add_building(-3, 4, 3, 6)         # blocks +y
        self._add_agent('hidden_x', 0, 2)
        self._add_agent('hidden_y', 2, 0)
        self._add_agent('visible',  1, 1)
        s = self.occluded_agent(sensor_range=35.0)
        s.sense(self.nid(0, 0))
        self.assertNotIn('hidden_x', s.data)
        self.assertNotIn('hidden_y', s.data)
        self.assertIn('visible', s.data)

    def test_agent_out_of_range_not_detected(self):
        self._add_agent('far', 4, 4)
        s = self.occluded_agent(sensor_range=15.0)
        s.sense(self.nid(0, 0))
        self.assertNotIn('far', s.data)


# ---------------------------------------------------------------------------
# Aerial sensor — grid scenarios
# ---------------------------------------------------------------------------

class OccludedAerialSensorTest(GridTest):
    """Drone looks down at the grid; building occluded nodes from low altitude."""

    def _make_drone(self, name, z):
        drone = self.ctx.agent.create_agent(
            name,
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=self.nid(0, 0),
            speed=5.0,
        )
        drone.position = (0.0, 0.0, z)
        return drone

    def test_drone_high_above_building_sees_all(self):
        # Drone at 30 m — rays steep enough to clear the 8 m wall entirely.
        self.add_building(4, -3, 6, 3)
        drone = self._make_drone('drone', z=30.0)
        s = self.occluded_aerial(sensor_range=60.0, fov=math.pi)
        s.set_owner(drone.name)
        s.sense(self.nid(0, 0))
        # High angle: node (0,1) should still be visible despite the wall.
        self.assertIn(self.nid(0, 1), s.data['nodes'])

    def test_drone_at_eye_level_loses_node_behind_wall(self):
        # Drone at 1 m — nearly horizontal sightline, 8 m wall blocks it.
        self.add_building(4, -3, 6, 3)
        drone = self._make_drone('drone_low', z=1.0)
        s = self.occluded_aerial(
            sensor_range=60.0, fov=math.pi,
            quat=(math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0),
        )
        s.set_owner(drone.name)
        s.sense(self.nid(0, 0))
        self.assertNotIn(self.nid(0, 1), s.data['nodes'])

    def test_drone_side_node_always_visible(self):
        # Node (1,0) is above the origin in y — the wall along x=5 never crosses this ray.
        self.add_building(4, -3, 6, 3)
        drone = self._make_drone('drone', z=5.0)
        s = self.occluded_aerial(sensor_range=60.0, fov=math.pi)
        s.set_owner(drone.name)
        s.sense(self.nid(0, 0))
        self.assertIn(self.nid(1, 0), s.data['nodes'])


# ---------------------------------------------------------------------------
# Aerial agent sensor — grid scenarios
# ---------------------------------------------------------------------------

class OccludedAerialAgentSensorTest(GridTest):
    """Drone detecting ground agents through (or past) a building."""

    def _make_drone(self, name, z):
        drone = self.ctx.agent.create_agent(
            name,
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=self.nid(0, 0),
            speed=5.0,
        )
        drone.position = (0.0, 0.0, z)
        return drone

    def _add_agent(self, name, row, col):
        return self.ctx.agent.create_agent(name, start_node_id=self.nid(row, col))

    def _sense(self, drone, label='occ_aa', **kwargs):
        s = self.occluded_aerial_agent(label, sensor_range=60.0,
                                        fov=math.pi, **kwargs)
        s.set_owner(drone.name)
        s.sense(self.nid(0, 0))
        return s.data

    def test_no_building_sees_all_agents(self):
        self._add_agent('a1', 0, 1)
        self._add_agent('a2', 1, 0)
        drone = self._make_drone('drone', z=5.0)
        data = self._sense(drone)
        self.assertIn('a1', data)
        self.assertIn('a2', data)

    def test_high_drone_sees_agent_behind_building(self):
        self.add_building(4, -3, 6, 3)
        self._add_agent('hidden_low', 0, 1)
        drone = self._make_drone('drone_high', z=25.0)
        data = self._sense(drone, label='occ_aa_high')
        self.assertIn('hidden_low', data)

    def test_low_drone_loses_agent_behind_building(self):
        self.add_building(4, -3, 6, 3)
        self._add_agent('hidden', 0, 1)
        drone = self._make_drone('drone_low', z=1.0)
        data = self._sense(drone, label='occ_aa_low')
        self.assertNotIn('hidden', data)

    def test_drone_never_detects_itself(self):
        drone = self._make_drone('drone', z=5.0)
        data = self._sense(drone)
        self.assertNotIn('drone', data)

    def test_data_format_is_type_and_position(self):
        self._add_agent('a1', 1, 1)
        drone = self._make_drone('drone', z=5.0)
        data = self._sense(drone)
        self.assertIn('a1', data)
        atype, pos = data['a1']
        self.assertEqual(len(pos), 3)


def suite():
    classes = [
        SegmentTriangleTest,
        QuadBlocksTest,
        QuadBlocksBatchTest,
        OccludedMapSensorTest,
        OccludedMapFovTest,
        OccludedAgentSensorTest,
        OccludedAerialSensorTest,
        OccludedAerialAgentSensorTest,
    ]
    s = unittest.TestSuite()
    for cls in classes:
        s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return s


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
