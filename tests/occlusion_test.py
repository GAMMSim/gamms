import math
import unittest

import numpy as np

import gamms
import gamms.typing
from gamms.SensorEngine.sensors_occluded import (
    _segment_triangle,
    _quad_blocks,
    _quad_blocks_batch,
)


# ---------------------------------------------------------------------------
# Minimal face stub
# ---------------------------------------------------------------------------

class _Face:
    def __init__(self, tl, tr, br, bl):
        self.tl = tl
        self.tr = tr
        self.br = br
        self.bl = bl


# A 1×1 vertical wall at x=5, spanning y in [-0.5, 0.5], z in [0, 2].
#   tl=(5,-0.5,2)  tr=(5, 0.5,2)
#   bl=(5,-0.5,0)  br=(5, 0.5,0)
WALL = _Face(
    tl=(5.0, -0.5, 2.0),
    tr=(5.0,  0.5, 2.0),
    br=(5.0,  0.5, 0.0),
    bl=(5.0, -0.5, 0.0),
)


# ---------------------------------------------------------------------------
# _segment_triangle  (scalar Möller-Trumbore)
# ---------------------------------------------------------------------------

class SegmentTriangleTest(unittest.TestCase):

    # Triangle in the plane x=5, y in [-1,1], z in [0,2]
    V0 = (5.0, -1.0, 0.0)
    V1 = (5.0,  1.0, 0.0)
    V2 = (5.0,  0.0, 2.0)

    def _hit(self, a, b):
        return _segment_triangle(a, b, self.V0, self.V1, self.V2)

    def test_direct_hit(self):
        self.assertTrue(self._hit((0, 0, 1), (10, 0, 1)))

    def test_miss_beside(self):
        self.assertFalse(self._hit((0, 5, 1), (10, 5, 1)))

    def test_miss_over(self):
        self.assertFalse(self._hit((0, 0, 3), (10, 0, 3)))

    def test_miss_under(self):
        self.assertFalse(self._hit((0, 0, -1), (10, 0, -1)))

    def test_segment_too_short(self):
        # Segment stops at x=4 — never reaches x=5.
        self.assertFalse(self._hit((0, 0, 1), (4, 0, 1)))

    def test_parallel_ray(self):
        # Ray parallel to the triangle plane; no intersection.
        self.assertFalse(self._hit((0, 0, 1), (0, 1, 1)))

    def test_origin_on_triangle_plane(self):
        # Start exactly on the triangle plane — t=0 is valid.
        self.assertTrue(self._hit((5, 0, 1), (10, 0, 1)))


# ---------------------------------------------------------------------------
# _quad_blocks  (scalar, two-triangle decomp)
# ---------------------------------------------------------------------------

class QuadBlocksTest(unittest.TestCase):

    def test_ray_hits_wall(self):
        self.assertTrue(_quad_blocks((0, 0, 1), (10, 0, 1), WALL))

    def test_ray_misses_beside(self):
        self.assertFalse(_quad_blocks((0, 5, 1), (10, 5, 1), WALL))

    def test_ray_passes_over(self):
        self.assertFalse(_quad_blocks((0, 0, 3), (10, 0, 3), WALL))

    def test_ray_passes_under(self):
        self.assertFalse(_quad_blocks((0, 0, -1), (10, 0, -1), WALL))

    def test_segment_stops_before_wall(self):
        self.assertFalse(_quad_blocks((0, 0, 1), (4, 0, 1), WALL))

    def test_both_endpoints_same_side(self):
        # Both points behind the wall — segment does not cross it.
        self.assertFalse(_quad_blocks((6, 0, 1), (8, 0, 1), WALL))

    def test_origin_behind_wall(self):
        # Observer already past the wall — segment goes further away.
        self.assertFalse(_quad_blocks((7, 0, 1), (10, 0, 1), WALL))


# ---------------------------------------------------------------------------
# _quad_blocks_batch  (numpy)
# ---------------------------------------------------------------------------

class QuadBlocksBatchTest(unittest.TestCase):

    O = np.array([0.0, 0.0, 1.0])

    def test_all_blocked(self):
        # Multiple targets behind the wall at x=5, all along y=0.
        T = np.array([[10.0, 0.0, 1.0], [12.0, 0.0, 1.0]])
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertTrue(result.all())

    def test_none_blocked(self):
        # Targets beside the wall.
        T = np.array([[10.0, 5.0, 1.0], [10.0, -5.0, 1.0]])
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertFalse(result.any())

    def test_mixed(self):
        T = np.array([
            [10.0,  0.0, 1.0],   # blocked
            [10.0,  5.0, 1.0],   # not blocked (beside)
            [10.0,  0.0, 5.0],   # not blocked (well above wall top at z=2)
        ])
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertEqual(list(result), [True, False, False])

    def test_empty_input(self):
        T = np.zeros((0, 3))
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertEqual(len(result), 0)

    def test_single_blocked(self):
        T = np.array([[10.0, 0.0, 1.0]])
        result = _quad_blocks_batch(self.O, T, WALL)
        self.assertTrue(result[0])


# ---------------------------------------------------------------------------
# End-to-end sensor tests
# ---------------------------------------------------------------------------

class OccludedSensorTest(unittest.TestCase):

    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={'level': 'CRITICAL'},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        # Two nodes: one behind a wall, one off to the side.
        self.ctx.graph.graph.add_node({'id': 0, 'x': 0.0,  'y': 0.0})
        self.ctx.graph.graph.add_node({'id': 1, 'x': 10.0, 'y': 0.0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 10.0, 'y': 10.0})
        self.ctx.graph.graph.add_edge({'id': 0, 'source': 0, 'target': 1, 'length': 10})
        self.ctx.graph.graph.add_edge({'id': 1, 'source': 0, 'target': 2, 'length': 14.14})

    def tearDown(self):
        self.ctx.terminate()

    def _add_blocking_wall(self):
        coords = [(4.5, -3.0), (5.5, -3.0), (5.5, 3.0), (4.5, 3.0)]
        height = 8.0
        n = len(coords)
        for i in range(n):
            p1, p2 = coords[i], coords[(i + 1) % n]
            self.ctx.graph.add_obstacle_face(
                i,
                tr=(p2[0], p2[1], height),
                tl=(p1[0], p1[1], height),
                br=(p2[0], p2[1], 0.0),
                bl=(p1[0], p1[1], 0.0),
                type=0,
            )

    def test_no_faces_matches_baseline(self):
        sensor = self.ctx.sensor.create_sensor(
            'no_faces', gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        sensor.sense(0)
        self.assertIn(1, sensor.data['nodes'])
        self.assertIn(2, sensor.data['nodes'])

    def test_wall_hides_node_behind_it(self):
        self._add_blocking_wall()
        baseline = self.ctx.sensor.create_sensor(
            'baseline', gamms.typing.SensorType.RANGE, sensor_range=20.0,
        )
        baseline.sense(0)
        self.assertIn(1, baseline.data['nodes'])

        occluded = self.ctx.sensor.create_sensor(
            'occluded', gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        occluded.sense(0)
        self.assertNotIn(1, occluded.data['nodes'])
        self.assertIn(2, occluded.data['nodes'])

    def test_wall_hides_agent_behind_it(self):
        self._add_blocking_wall()
        self.ctx.agent.create_agent('hidden',  start_node_id=1)
        self.ctx.agent.create_agent('visible', start_node_id=2)

        sensor = self.ctx.sensor.create_sensor(
            'occluded_agent',
            gamms.typing.SensorType.OCCLUDED_AGENT,
            sensor_range=30.0,
        )
        sensor.sense(0)
        self.assertNotIn('hidden',  sensor.data)
        self.assertIn('visible', sensor.data)

    def test_face_outside_range_ignored(self):
        self._add_blocking_wall()
        far = [(500.0, 500.0), (510.0, 500.0), (510.0, 510.0), (500.0, 510.0)]
        for i in range(4):
            p1, p2 = far[i], far[(i + 1) % 4]
            self.ctx.graph.add_obstacle_face(
                99 * 10000 + i,
                tr=(p2[0], p2[1], 20.0),
                tl=(p1[0], p1[1], 20.0),
                br=(p2[0], p2[1], 0.0),
                bl=(p1[0], p1[1], 0.0),
                type=0,
            )
        sensor = self.ctx.sensor.create_sensor(
            'filtered', gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        sensor.sense(0)
        self.assertNotIn(1, sensor.data['nodes'])
        self.assertIn(2, sensor.data['nodes'])

    def test_aerial_above_wall_sees_blocked_node(self):
        self._add_blocking_wall()
        aerial = self.ctx.agent.create_agent(
            name='drone',
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        aerial.position = (0.0, 0.0, 20.0)

        sensor = self.ctx.sensor.create_sensor(
            'aerial_high',
            gamms.typing.SensorType.OCCLUDED_AERIAL,
            sensor_range=50.0,
            fov=math.pi,
        )
        sensor.set_owner(aerial.name)
        sensor.sense(0)
        self.assertIn(1, sensor.data['nodes'])

    def test_aerial_low_loses_node_behind_wall(self):
        self._add_blocking_wall()
        aerial = self.ctx.agent.create_agent(
            name='drone_low',
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        aerial.position = (0.0, 0.0, 1.0)

        sensor = self.ctx.sensor.create_sensor(
            'aerial_low',
            gamms.typing.SensorType.OCCLUDED_AERIAL,
            sensor_range=50.0,
            fov=math.pi,
            quat=(math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0),
        )
        sensor.set_owner(aerial.name)
        sensor.sense(0)
        self.assertNotIn(1, sensor.data['nodes'])


def suite():
    s = unittest.TestSuite()
    for cls in (SegmentTriangleTest, QuadBlocksTest, QuadBlocksBatchTest, OccludedSensorTest):
        s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return s


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
