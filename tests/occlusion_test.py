"""
Occlusion sensor tests.

Coordinate system: x/y are projected metres (UTM), z is height in metres.
Observer eye-level defaults to 1.6 m.  All geometry is exact — no tolerances
unless the test is specifically probing a boundary.
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
# Reusable geometry fixtures
# ---------------------------------------------------------------------------

class _Face:
    """Minimal ObsFace stub: four 3-D corners (tl, tr, br, bl)."""
    __slots__ = ("tl", "tr", "br", "bl")

    def __init__(self, tl, tr, br, bl):
        self.tl = tl
        self.tr = tr
        self.br = br
        self.bl = bl


# 1 m wide × 2 m tall vertical wall sitting at x=5, centred on y=0.
WALL = _Face(
    tl=(5.0, -0.5, 2.0),
    tr=(5.0,  0.5, 2.0),
    br=(5.0,  0.5, 0.0),
    bl=(5.0, -0.5, 0.0),
)

# Larger wall — 10 m wide × 8 m tall — for end-to-end sensor tests.
def _blocking_wall_faces():
    """Four ObsFace quads forming a box wall between x=4.5 and x=5.5."""
    coords = [(4.5, -3.0), (5.5, -3.0), (5.5, 3.0), (4.5, 3.0)]
    height = 8.0
    faces = []
    n = len(coords)
    for i in range(n):
        p1, p2 = coords[i], coords[(i + 1) % n]
        faces.append({
            "id": i,
            "tr": (p2[0], p2[1], height),
            "tl": (p1[0], p1[1], height),
            "br": (p2[0], p2[1], 0.0),
            "bl": (p1[0], p1[1], 0.0),
        })
    return faces


# ---------------------------------------------------------------------------
# _segment_triangle — scalar Möller-Trumbore
# ---------------------------------------------------------------------------
#
# Triangle lives in the plane x = 5:
#   v0 = (5, -1, 0)   bottom-left
#   v1 = (5,  1, 0)   bottom-right
#   v2 = (5,  0, 2)   apex
#

class SegmentTriangleTest(unittest.TestCase):

    V0 = (5.0, -1.0, 0.0)
    V1 = (5.0,  1.0, 0.0)
    V2 = (5.0,  0.0, 2.0)

    def _hit(self, a, b):
        return _segment_triangle(a, b, self.V0, self.V1, self.V2)

    # --- basic hits ---

    def test_centre_hit(self):
        # Straight through the centroid of the triangle.
        self.assertTrue(self._hit((0, 0, 0.67), (10, 0, 0.67)))

    def test_near_apex(self):
        self.assertTrue(self._hit((0, 0, 1.9), (10, 0, 1.9)))

    def test_near_base_left(self):
        self.assertTrue(self._hit((0, -0.9, 0.05), (10, -0.9, 0.05)))

    # --- misses ---

    def test_miss_above_apex(self):
        # z=2.1 clears the apex (z=2).
        self.assertFalse(self._hit((0, 0, 2.1), (10, 0, 2.1)))

    def test_miss_below_base(self):
        self.assertFalse(self._hit((0, 0, -0.1), (10, 0, -0.1)))

    def test_miss_left_of_triangle(self):
        # y=-1.1 is outside the base edge.
        self.assertFalse(self._hit((0, -1.1, 0.5), (10, -1.1, 0.5)))

    def test_miss_right_of_triangle(self):
        self.assertFalse(self._hit((0, 1.1, 0.5), (10, 1.1, 0.5)))

    # --- segment length ---

    def test_segment_stops_before_plane(self):
        # Segment ends at x=4.99 — doesn't quite reach x=5.
        self.assertFalse(self._hit((0, 0, 0.67), (4.99, 0, 0.67)))

    def test_segment_endpoint_exactly_on_triangle(self):
        # b lies on the triangle — t=1 is the boundary, should count.
        self.assertTrue(self._hit((0, 0, 0.67), (5, 0, 0.67)))

    def test_segment_starts_past_triangle(self):
        # Both endpoints are on the far side; t would be negative.
        self.assertFalse(self._hit((6, 0, 0.67), (10, 0, 0.67)))

    # --- degenerate / edge cases ---

    def test_parallel_to_plane(self):
        # Ray runs parallel to x=5 — should never hit.
        self.assertFalse(self._hit((0, 0, 1), (0, 10, 1)))

    def test_zero_length_segment(self):
        # Degenerate: a == b, direction is zero — effectively parallel.
        self.assertFalse(self._hit((5, 0, 0.67), (5, 0, 0.67)))

    def test_ray_in_triangle_plane(self):
        # Segment lies entirely within x=5; Möller-Trumbore treats this as
        # parallel (determinant → 0).
        self.assertFalse(self._hit((5, -0.5, 0.5), (5, 0.5, 0.5)))

    def test_reversed_direction_still_hits(self):
        # Möller-Trumbore is direction-agnostic for segment tests; going from
        # x=10 back toward x=0 should still find the intersection.
        self.assertTrue(self._hit((10, 0, 0.67), (0, 0, 0.67)))

    def test_origin_on_triangle(self):
        # Observer starts exactly on the triangle surface — t=0 is valid.
        self.assertTrue(self._hit((5, 0, 0.67), (10, 0, 0.67)))


# ---------------------------------------------------------------------------
# _quad_blocks — scalar two-triangle decomposition
# ---------------------------------------------------------------------------

class QuadBlocksTest(unittest.TestCase):
    """Tests against the unit WALL fixture (x=5, y∈[-0.5,0.5], z∈[0,2])."""

    # --- definite hits ---

    def test_horizontal_ray_through_centre(self):
        self.assertTrue(_quad_blocks((0, 0, 1), (10, 0, 1), WALL))

    def test_angled_ray_still_hits(self):
        # Diagonal approach — not purely horizontal.
        self.assertTrue(_quad_blocks((0, -0.4, 0.5), (10, 0.4, 1.5), WALL))

    def test_hit_lower_triangle(self):
        # The lower-left triangle (tl-br-bl) of the quad.
        # Low z, slightly negative y — only the second triangle covers this.
        self.assertTrue(_quad_blocks((0, -0.4, 0.1), (10, -0.4, 0.1), WALL))

    def test_hit_upper_triangle(self):
        # The upper-right triangle (tl-tr-br).  High z, positive y.
        self.assertTrue(_quad_blocks((0, 0.4, 1.8), (10, 0.4, 1.8), WALL))

    # --- definite misses ---

    def test_miss_wide_left(self):
        self.assertFalse(_quad_blocks((0, -2, 1), (10, -2, 1), WALL))

    def test_miss_wide_right(self):
        self.assertFalse(_quad_blocks((0, 2, 1), (10, 2, 1), WALL))

    def test_miss_above_wall(self):
        # z=2.5 > wall top (z=2).
        self.assertFalse(_quad_blocks((0, 0, 2.5), (10, 0, 2.5), WALL))

    def test_miss_below_wall(self):
        self.assertFalse(_quad_blocks((0, 0, -0.5), (10, 0, -0.5), WALL))

    # --- segment boundary ---

    def test_segment_does_not_reach_wall(self):
        self.assertFalse(_quad_blocks((0, 0, 1), (4.9, 0, 1), WALL))

    def test_both_endpoints_behind_wall(self):
        # Observer and target are both past x=5; no crossing.
        self.assertFalse(_quad_blocks((6, 0, 1), (9, 0, 1), WALL))

    def test_observer_is_behind_wall(self):
        # Observer already on the far side; ray travels further away.
        self.assertFalse(_quad_blocks((7, 0, 1), (12, 0, 1), WALL))

    # --- non-axis-aligned face ---

    def test_diagonal_wall(self):
        # Wall tilted 45° in plan view, spanning from (3,3) to (7,7) at z∈[0,4].
        diag = _Face(
            tl=(3.0, 3.0, 4.0),
            tr=(7.0, 7.0, 4.0),
            br=(7.0, 7.0, 0.0),
            bl=(3.0, 3.0, 0.0),
        )
        # Ray goes straight through the middle of the diagonal wall.
        self.assertTrue(_quad_blocks((0, 5, 2), (10, 5, 2), diag))

    def test_diagonal_wall_miss_parallel(self):
        diag = _Face(
            tl=(3.0, 3.0, 4.0),
            tr=(7.0, 7.0, 4.0),
            br=(7.0, 7.0, 0.0),
            bl=(3.0, 3.0, 0.0),
        )
        # Ray runs parallel to the diagonal wall and doesn't cross.
        self.assertFalse(_quad_blocks((0, 8, 2), (10, 8, 2), diag))


# ---------------------------------------------------------------------------
# _quad_blocks_batch — numpy vectorised
# ---------------------------------------------------------------------------

class QuadBlocksBatchTest(unittest.TestCase):

    O = np.array([0.0, 0.0, 1.0])

    # --- trivial size cases ---

    def test_empty_input_returns_empty(self):
        result = _quad_blocks_batch(self.O, np.zeros((0, 3)), WALL)
        self.assertEqual(len(result), 0)
        self.assertEqual(result.dtype, bool)

    def test_single_target_blocked(self):
        T = np.array([[10.0, 0.0, 1.0]])
        self.assertTrue(_quad_blocks_batch(self.O, T, WALL)[0])

    def test_single_target_not_blocked(self):
        T = np.array([[10.0, 5.0, 1.0]])
        self.assertFalse(_quad_blocks_batch(self.O, T, WALL)[0])

    # --- batch correctness ---

    def test_all_blocked(self):
        T = np.array([
            [10.0, 0.0, 0.5],
            [12.0, 0.0, 1.0],
            [15.0, 0.2, 1.5],
        ])
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertTrue(result.all())

    def test_none_blocked(self):
        T = np.array([
            [10.0,  5.0, 1.0],   # way off to the side
            [10.0, -5.0, 1.0],
            [ 3.0,  0.0, 1.0],   # in front of wall
            [10.0,  0.0, 5.0],   # over the wall (z=5 clears top edge at z=2)
        ])
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertFalse(result.any())

    def test_mixed_results(self):
        T = np.array([
            [10.0,  0.0, 1.0],   # blocked — straight through
            [10.0,  5.0, 1.0],   # not blocked — beside
            [10.0,  0.0, 5.0],   # not blocked — well above (ray passes over z=2 top)
            [10.0, -0.4, 0.2],   # blocked — lower triangle
            [ 3.0,  0.0, 1.0],   # not blocked — doesn't reach wall
        ])
        result = _quad_blocks_batch(self.O, T, WALL)
        expected = [True, False, False, True, False]
        self.assertEqual(list(result), expected)

    def test_result_is_boolean_array(self):
        T = np.array([[10.0, 0.0, 1.0], [10.0, 5.0, 1.0]])
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertEqual(result.dtype, bool)
        self.assertEqual(result.shape, (2,))

    def test_large_batch_consistent_with_scalar(self):
        # Generate 200 targets and verify batch == scalar for each.
        rng = np.random.default_rng(42)
        targets = rng.uniform(low=[6, -3, 0], high=[15, 3, 4], size=(200, 3))
        O = self.O
        batch = _quad_blocks_batch(O, targets, WALL)
        for i, t in enumerate(targets):
            expected = _quad_blocks(tuple(O), tuple(t), WALL)  # type: ignore[arg-type]
            self.assertEqual(bool(batch[i]), expected,
                             msg=f"Mismatch at target {i}: {t}")


# ---------------------------------------------------------------------------
# End-to-end sensor tests
# ---------------------------------------------------------------------------

class OccludedSensorTest(unittest.TestCase):
    """
    Graph topology:

        0 ——— 1         wall lives between x=4.5 and x=5.5
        |
        2 (at y=10, diagonal from 0)

    Node 1 is directly behind the wall from node 0's perspective.
    Node 2 is off to the side — visible even with the wall present.
    """

    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={"level": "CRITICAL"},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        g = self.ctx.graph.graph
        g.add_node({"id": 0, "x":  0.0, "y":  0.0})
        g.add_node({"id": 1, "x": 10.0, "y":  0.0})
        g.add_node({"id": 2, "x": 10.0, "y": 10.0})
        g.add_edge({"id": 0, "source": 0, "target": 1, "length": 10.0})
        g.add_edge({"id": 1, "source": 0, "target": 2, "length": 14.14})

    def tearDown(self):
        self.ctx.terminate()

    def _add_wall(self):
        for f in _blocking_wall_faces():
            self.ctx.graph.add_obstacle_face(
                f["id"], tr=f["tr"], tl=f["tl"], br=f["br"], bl=f["bl"], type=0,
            )

    # --- baseline behaviour ---

    def test_no_faces_occluded_sensor_matches_range_sensor(self):
        # Without any obstacle faces the occluded sensor must be identical
        # to the plain range sensor.
        baseline = self.ctx.sensor.create_sensor(
            "base", gamms.typing.SensorType.RANGE, sensor_range=20.0,
        )
        occluded = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        baseline.sense(0)
        occluded.sense(0)
        self.assertEqual(
            set(baseline.data["nodes"].keys()),
            set(occluded.data["nodes"].keys()),
        )

    def test_observer_node_always_visible(self):
        # The node the agent is standing on must never be filtered out.
        self._add_wall()
        sensor = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        sensor.sense(0)
        self.assertIn(0, sensor.data["nodes"])

    # --- wall occlusion ---

    def test_wall_hides_node_directly_behind(self):
        self._add_wall()
        sensor = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        sensor.sense(0)
        self.assertNotIn(1, sensor.data["nodes"])

    def test_wall_does_not_hide_node_to_the_side(self):
        self._add_wall()
        sensor = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        sensor.sense(0)
        self.assertIn(2, sensor.data["nodes"])

    def test_edge_hidden_when_both_endpoints_occluded(self):
        # Add a third node also directly behind the wall.
        self.ctx.graph.graph.add_node({"id": 3, "x": 12.0, "y": 0.5})
        self.ctx.graph.graph.add_edge(
            {"id": 2, "source": 1, "target": 3, "length": 2.1}
        )
        self._add_wall()
        sensor = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=25.0,
        )
        sensor.sense(0)
        visible_ids = set(sensor.data["nodes"].keys())
        # Both endpoints hidden → edge must not appear either.
        for edge in sensor.data["edges"]:
            self.assertTrue(
                edge.source in visible_ids and edge.target in visible_ids,
                msg=f"Edge {edge.source}→{edge.target} leaked into sensor output",
            )

    # --- range filtering ---

    def test_wall_outside_sensor_range_ignored(self):
        # Wall is at x≈5, sensor range only 4 m — the wall is outside range
        # but both nodes 1 and 2 are also outside range.  We use a separate
        # far wall to ensure range filtering is working.
        far = [(100.0, -3.0), (101.0, -3.0), (101.0, 3.0), (100.0, 3.0)]
        for i in range(4):
            p1, p2 = far[i], far[(i + 1) % 4]
            self.ctx.graph.add_obstacle_face(
                200 + i,
                tr=(p2[0], p2[1], 8.0),
                tl=(p1[0], p1[1], 8.0),
                br=(p2[0], p2[1], 0.0),
                bl=(p1[0], p1[1], 0.0),
                type=0,
            )
        # The far wall is 100 m away; sensor range is 20 m — it must be ignored.
        self._add_wall()
        sensor = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        sensor.sense(0)
        self.assertNotIn(1, sensor.data["nodes"])   # near wall still occludes
        self.assertIn(2, sensor.data["nodes"])      # side node still visible

    # --- agent sensor ---

    def test_agent_sensor_hides_agent_behind_wall(self):
        self._add_wall()
        self.ctx.agent.create_agent("behind_wall", start_node_id=1)
        self.ctx.agent.create_agent("clear_los",   start_node_id=2)

        sensor = self.ctx.sensor.create_sensor(
            "occ_agent",
            gamms.typing.SensorType.OCCLUDED_AGENT,
            sensor_range=30.0,
        )
        sensor.sense(0)
        self.assertNotIn("behind_wall", sensor.data)
        self.assertIn("clear_los", sensor.data)

    def test_agent_sensor_no_false_positives_without_wall(self):
        self.ctx.agent.create_agent("a1", start_node_id=1)
        self.ctx.agent.create_agent("a2", start_node_id=2)

        sensor = self.ctx.sensor.create_sensor(
            "occ_agent",
            gamms.typing.SensorType.OCCLUDED_AGENT,
            sensor_range=30.0,
        )
        sensor.sense(0)
        # No walls → both agents visible.
        self.assertIn("a1", sensor.data)
        self.assertIn("a2", sensor.data)

    # --- aerial sensor ---

    def test_aerial_high_above_wall_sees_occluded_node(self):
        # A drone at z=20 m sends rays nearly straight down — they miss the
        # 8 m wall and node 1 should remain visible.
        self._add_wall()
        drone = self.ctx.agent.create_agent(
            "drone",
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        drone.position = (0.0, 0.0, 20.0)

        sensor = self.ctx.sensor.create_sensor(
            "aerial_occ",
            gamms.typing.SensorType.OCCLUDED_AERIAL,
            sensor_range=50.0,
            fov=math.pi,
        )
        sensor.set_owner(drone.name)
        sensor.sense(0)
        self.assertIn(1, sensor.data["nodes"])

    def test_aerial_at_eye_level_loses_node_behind_wall(self):
        # Same drone, now hovering at 1 m — its sightline to node 1 is nearly
        # horizontal and the 8 m wall blocks it.
        self._add_wall()
        drone = self.ctx.agent.create_agent(
            "drone_low",
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        drone.position = (0.0, 0.0, 1.0)

        sensor = self.ctx.sensor.create_sensor(
            "aerial_low",
            gamms.typing.SensorType.OCCLUDED_AERIAL,
            sensor_range=50.0,
            fov=math.pi,
            quat=(math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0),
        )
        sensor.set_owner(drone.name)
        sensor.sense(0)
        self.assertNotIn(1, sensor.data["nodes"])

    def test_aerial_intermediate_height_side_node_visible(self):
        # Node 2 is off to the side — wall never occludes it regardless of
        # drone altitude.
        self._add_wall()
        drone = self.ctx.agent.create_agent(
            "drone_mid",
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        drone.position = (0.0, 0.0, 3.0)

        sensor = self.ctx.sensor.create_sensor(
            "aerial_mid",
            gamms.typing.SensorType.OCCLUDED_AERIAL,
            sensor_range=50.0,
            fov=math.pi,
        )
        sensor.set_owner(drone.name)
        sensor.sense(0)
        self.assertIn(2, sensor.data["nodes"])


# ---------------------------------------------------------------------------
# FOV + occlusion interaction
# ---------------------------------------------------------------------------

class FovOcclusionTest(unittest.TestCase):
    """
    Graph:

        3(-10,0) --- 0(0,0) --- 1(10,0)
                        |
                     2(0,10)

    Sensor orientation=(1,0) — facing +x.  FOV=π/2 (±45°).

    Node 1 is in the cone AND behind the wall.
    Node 2 is off to the side — outside the cone, clear LOS.
    Node 3 is directly behind the observer — outside the cone, clear LOS.
    """

    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={"level": "CRITICAL"},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        g = self.ctx.graph.graph
        g.add_node({"id": 0, "x":   0.0, "y":  0.0})
        g.add_node({"id": 1, "x":  10.0, "y":  0.0})
        g.add_node({"id": 2, "x":   0.0, "y": 10.0})
        g.add_node({"id": 3, "x": -10.0, "y":  0.0})
        g.add_edge({"id": 0, "source": 0, "target": 1, "length": 10.0})
        g.add_edge({"id": 1, "source": 0, "target": 2, "length": 10.0})
        g.add_edge({"id": 2, "source": 0, "target": 3, "length": 10.0})

    def tearDown(self):
        self.ctx.terminate()

    def _add_wall(self):
        for f in _blocking_wall_faces():
            self.ctx.graph.add_obstacle_face(
                f["id"], tr=f["tr"], tl=f["tl"], br=f["br"], bl=f["bl"], type=0,
            )

    def _make_sensor(self, fov):
        return self.ctx.sensor.create_sensor(
            "occ",
            gamms.typing.SensorType.OCCLUDED_MAP,
            sensor_range=20.0,
            fov=fov,
            orientation=(1.0, 0.0),   # fixed +x facing, no owner needed
        )

    def test_fov_excludes_side_node_without_wall(self):
        # Node 2 is at 90° from the +x orientation — outside π/2 cone.
        sensor = self._make_sensor(math.pi / 2)
        sensor.sense(0)
        self.assertNotIn(2, sensor.data["nodes"])

    def test_fov_excludes_behind_node_without_wall(self):
        # Node 3 is directly behind the observer.
        sensor = self._make_sensor(math.pi / 2)
        sensor.sense(0)
        self.assertNotIn(3, sensor.data["nodes"])

    def test_fov_keeps_forward_node_without_wall(self):
        # Node 1 is straight ahead — inside the cone.
        sensor = self._make_sensor(math.pi / 2)
        sensor.sense(0)
        self.assertIn(1, sensor.data["nodes"])

    def test_fov_and_wall_both_exclude(self):
        # Node 1 is inside the cone but behind the wall.
        # Node 2 is outside the cone and has clear LOS.
        # Both must be absent from the output, for different reasons.
        self._add_wall()
        sensor = self._make_sensor(math.pi / 2)
        sensor.sense(0)
        self.assertNotIn(1, sensor.data["nodes"])   # blocked by wall
        self.assertNotIn(2, sensor.data["nodes"])   # cut by FOV
        self.assertNotIn(3, sensor.data["nodes"])   # cut by FOV (behind)

    def test_full_fov_with_wall_only_blocks_occluded_node(self):
        # 2π FOV — FOV filter is completely off, only the wall matters.
        self._add_wall()
        sensor = self._make_sensor(2 * math.pi)
        sensor.sense(0)
        self.assertNotIn(1, sensor.data["nodes"])   # wall occludes
        self.assertIn(2, sensor.data["nodes"])      # side — clear LOS
        self.assertIn(3, sensor.data["nodes"])      # behind observer — clear LOS

    def test_wide_fov_includes_diagonal_node(self):
        # 3π/2 cone (270°) should include node 2 at 90° and node 1 straight ahead.
        sensor = self._make_sensor(3 * math.pi / 2)
        sensor.sense(0)
        self.assertIn(1, sensor.data["nodes"])
        self.assertIn(2, sensor.data["nodes"])
        self.assertNotIn(3, sensor.data["nodes"])   # 180° is still outside 270÷2=135° half-angle


# ---------------------------------------------------------------------------
# Multiple walls — accumulation path
# ---------------------------------------------------------------------------

class MultipleWallsTest(unittest.TestCase):
    """
    Two independent walls, each occluding a different node.

        0(0,0) ——— 1(10,0)      wall A at x≈5 blocks node 1
           \
            2(10,10)             wall B at the midpoint blocks node 2

    Verifies that the per-face accumulation loop correctly applies both
    walls, and that early-exit doesn't fire too soon.
    """

    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={"level": "CRITICAL"},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        g = self.ctx.graph.graph
        g.add_node({"id": 0, "x":  0.0, "y":  0.0})
        g.add_node({"id": 1, "x": 10.0, "y":  0.0})
        g.add_node({"id": 2, "x": 10.0, "y": 10.0})
        g.add_edge({"id": 0, "source": 0, "target": 1, "length": 10.0})
        g.add_edge({"id": 1, "source": 0, "target": 2, "length": 14.14})

    def tearDown(self):
        self.ctx.terminate()

    def _add_wall_a(self):
        """Blocks node 1 (along +x axis)."""
        for f in _blocking_wall_faces():   # wall at x≈5, y∈[-3,3]
            self.ctx.graph.add_obstacle_face(
                f["id"], tr=f["tr"], tl=f["tl"], br=f["br"], bl=f["bl"], type=0,
            )

    def _add_wall_b(self):
        """Blocks node 2 (diagonal at ~45°).
        Wall sits at (5,5), perpendicular to the x=y diagonal."""
        # A wide slab spanning x∈[2,8] at y≈5, tall enough to matter.
        coords = [(2.0, 4.5), (8.0, 4.5), (8.0, 5.5), (2.0, 5.5)]
        height = 8.0
        n = len(coords)
        for i in range(n):
            p1, p2 = coords[i], coords[(i + 1) % n]
            self.ctx.graph.add_obstacle_face(
                100 + i,
                tr=(p2[0], p2[1], height),
                tl=(p1[0], p1[1], height),
                br=(p2[0], p2[1], 0.0),
                bl=(p1[0], p1[1], 0.0),
                type=0,
            )

    def test_single_wall_a_blocks_only_node1(self):
        self._add_wall_a()
        s = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        s.sense(0)
        self.assertNotIn(1, s.data["nodes"])
        self.assertIn(2, s.data["nodes"])

    def test_single_wall_b_blocks_only_node2(self):
        self._add_wall_b()
        s = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        s.sense(0)
        self.assertIn(1, s.data["nodes"])
        self.assertNotIn(2, s.data["nodes"])

    def test_both_walls_block_both_nodes(self):
        # Both walls present — accumulation must apply both independently.
        self._add_wall_a()
        self._add_wall_b()
        s = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        s.sense(0)
        self.assertNotIn(1, s.data["nodes"])
        self.assertNotIn(2, s.data["nodes"])

    def test_observer_node_survives_both_walls(self):
        self._add_wall_a()
        self._add_wall_b()
        s = self.ctx.sensor.create_sensor(
            "occ", gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        s.sense(0)
        self.assertIn(0, s.data["nodes"])


# ---------------------------------------------------------------------------
# Infinite sensor range
# ---------------------------------------------------------------------------

class InfiniteRangeTest(unittest.TestCase):
    """
    Verifies the _iter_faces / _face_ids_in_range code path that fires when
    sensor_range == inf.  In that branch get_obstacle_faces() is called with
    no spatial arguments, so all faces in the store are returned.
    """

    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={"level": "CRITICAL"},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        g = self.ctx.graph.graph
        g.add_node({"id": 0, "x":  0.0, "y":  0.0})
        g.add_node({"id": 1, "x": 10.0, "y":  0.0})
        g.add_node({"id": 2, "x": 10.0, "y": 10.0})
        # Far node — only reachable with infinite range.
        g.add_node({"id": 3, "x": 500.0, "y": 0.0})
        g.add_edge({"id": 0, "source": 0, "target": 1, "length": 10.0})
        g.add_edge({"id": 1, "source": 0, "target": 2, "length": 14.14})
        g.add_edge({"id": 2, "source": 0, "target": 3, "length": 500.0})

    def tearDown(self):
        self.ctx.terminate()

    def _add_wall(self):
        for f in _blocking_wall_faces():
            self.ctx.graph.add_obstacle_face(
                f["id"], tr=f["tr"], tl=f["tl"], br=f["br"], bl=f["bl"], type=0,
            )

    def test_infinite_range_sees_far_node_without_wall(self):
        s = self.ctx.sensor.create_sensor(
            "occ_inf", gamms.typing.SensorType.OCCLUDED_MAP,
            sensor_range=float("inf"),
        )
        s.sense(0)
        self.assertIn(3, s.data["nodes"])

    def test_infinite_range_still_occludes_near_node(self):
        # The wall is within the scene; even with infinite range it must
        # still block node 1.
        self._add_wall()
        s = self.ctx.sensor.create_sensor(
            "occ_inf", gamms.typing.SensorType.OCCLUDED_MAP,
            sensor_range=float("inf"),
        )
        s.sense(0)
        self.assertNotIn(1, s.data["nodes"])

    def test_infinite_range_side_node_still_visible(self):
        self._add_wall()
        s = self.ctx.sensor.create_sensor(
            "occ_inf", gamms.typing.SensorType.OCCLUDED_MAP,
            sensor_range=float("inf"),
        )
        s.sense(0)
        self.assertIn(2, s.data["nodes"])

    def test_infinite_range_far_node_clear_of_wall(self):
        # Node 3 is 500 m away along +x.  The wall at x≈5 IS between
        # node 0 and node 3 — it should occlude node 3 too.
        self._add_wall()
        s = self.ctx.sensor.create_sensor(
            "occ_inf", gamms.typing.SensorType.OCCLUDED_MAP,
            sensor_range=float("inf"),
        )
        s.sense(0)
        self.assertNotIn(3, s.data["nodes"])

    def test_infinite_range_agent_sensor(self):
        # OccludedAgentSensor with infinite range — takes the _face_ids_in_range
        # no-arg branch.
        self._add_wall()
        self.ctx.agent.create_agent("hidden",  start_node_id=1)
        self.ctx.agent.create_agent("visible", start_node_id=2)
        s = self.ctx.sensor.create_sensor(
            "occ_agent_inf", gamms.typing.SensorType.OCCLUDED_AGENT,
            sensor_range=float("inf"),
        )
        s.sense(0)
        self.assertNotIn("hidden",  s.data)
        self.assertIn("visible", s.data)


# ---------------------------------------------------------------------------
# OccludedAerialAgentSensor
# ---------------------------------------------------------------------------

class OccludedAerialAgentSensorTest(unittest.TestCase):
    """
    Drone observing ground agents through (or not through) the blocking wall.
    The sensor data format is Dict[str, (AgentType, (x, y, z))].
    """

    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={"level": "CRITICAL"},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        g = self.ctx.graph.graph
        g.add_node({"id": 0, "x":  0.0, "y":  0.0})
        g.add_node({"id": 1, "x": 10.0, "y":  0.0})   # behind wall
        g.add_node({"id": 2, "x": 10.0, "y": 10.0})   # clear LOS
        g.add_edge({"id": 0, "source": 0, "target": 1, "length": 10.0})
        g.add_edge({"id": 1, "source": 0, "target": 2, "length": 14.14})

    def tearDown(self):
        self.ctx.terminate()

    def _add_wall(self):
        for f in _blocking_wall_faces():
            self.ctx.graph.add_obstacle_face(
                f["id"], tr=f["tr"], tl=f["tl"], br=f["br"], bl=f["bl"], type=0,
            )

    def _make_drone(self, name, z):
        drone = self.ctx.agent.create_agent(
            name,
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        drone.position = (0.0, 0.0, z)
        return drone

    def _make_sensor(self, drone_name, label="aerial_agent_occ"):
        s = self.ctx.sensor.create_sensor(
            label,
            gamms.typing.SensorType.OCCLUDED_AERIAL_AGENT,
            sensor_range=50.0,
            fov=math.pi,
        )
        s.set_owner(drone_name)
        return s

    def test_no_wall_drone_sees_all_agents(self):
        self.ctx.agent.create_agent("a1", start_node_id=1)
        self.ctx.agent.create_agent("a2", start_node_id=2)
        drone = self._make_drone("drone", z=5.0)
        s = self._make_sensor(drone.name)
        s.sense(0)
        self.assertIn("a1", s.data)
        self.assertIn("a2", s.data)

    def test_high_drone_sees_agent_behind_wall(self):
        # At 20 m the ray descends steeply enough to clear the 8 m wall.
        self._add_wall()
        self.ctx.agent.create_agent("behind", start_node_id=1)
        drone = self._make_drone("drone", z=20.0)
        s = self._make_sensor(drone.name)
        s.sense(0)
        self.assertIn("behind", s.data)

    def test_low_drone_loses_agent_behind_wall(self):
        # At 1 m the sightline is almost horizontal — wall blocks it.
        self._add_wall()
        self.ctx.agent.create_agent("behind", start_node_id=1)
        drone = self._make_drone("drone_low", z=1.0)
        s = self._make_sensor(drone.name, label="aerial_agent_low")
        s.sense(0)
        self.assertNotIn("behind", s.data)

    def test_low_drone_keeps_agent_with_clear_los(self):
        self._add_wall()
        self.ctx.agent.create_agent("clear", start_node_id=2)
        drone = self._make_drone("drone_low2", z=1.0)
        s = self._make_sensor(drone.name, label="aerial_agent_clear")
        s.sense(0)
        self.assertIn("clear", s.data)

    def test_drone_does_not_detect_itself(self):
        drone = self._make_drone("drone", z=5.0)
        s = self._make_sensor(drone.name)
        s.sense(0)
        self.assertNotIn("drone", s.data)

    def test_data_contains_position_tuple(self):
        self.ctx.agent.create_agent("a1", start_node_id=2)
        drone = self._make_drone("drone", z=5.0)
        s = self._make_sensor(drone.name)
        s.sense(0)
        self.assertIn("a1", s.data)
        atype, pos = s.data["a1"]
        self.assertEqual(len(pos), 3)


def suite():
    s = unittest.TestSuite()
    for cls in (
        SegmentTriangleTest,
        QuadBlocksTest,
        QuadBlocksBatchTest,
        OccludedSensorTest,
        FovOcclusionTest,
        MultipleWallsTest,
        InfiniteRangeTest,
        OccludedAerialAgentSensorTest,
    ):
        s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return s


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
