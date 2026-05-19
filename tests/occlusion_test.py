import math
import unittest

import gamms
import gamms.typing
from gamms.SensorEngine.sensors_occluded import (
    segment_blocked_by_polygon,
    segment_blocked_by_polygons,
    segment_intersects_polygon_top,
)


SQUARE = [(2.0, -1.0), (3.0, -1.0), (3.0, 1.0), (2.0, 1.0)]


class OcclusionGeometryTest(unittest.TestCase):
    def test_low_ray_is_blocked(self):
        self.assertTrue(
            segment_blocked_by_polygon((0, 0, 1), (5, 0, 1), SQUARE, 0.0, 3.0)
        )

    def test_high_ray_passes_over(self):
        self.assertFalse(
            segment_blocked_by_polygon((0, 0, 10), (5, 0, 10), SQUARE, 0.0, 3.0)
        )

    def test_side_ray_misses(self):
        self.assertFalse(
            segment_blocked_by_polygon((0, 5, 1), (5, 5, 1), SQUARE, 0.0, 3.0)
        )

    def test_ray_starting_inside(self):
        self.assertTrue(
            segment_blocked_by_polygon((2.5, 0, 1), (5, 0, 1), SQUARE, 0.0, 3.0)
        )

    def test_top_face_blocked_when_descending(self):
        self.assertTrue(
            segment_intersects_polygon_top(
                (2.5, 0.0, 5.0), (2.5, 0.0, 0.0), SQUARE, 0.0, 3.0
            )
        )

    def test_segment_blocked_by_polygons_iterable(self):
        # Polygon list with two prisms; the ray hits the second one.
        far_square = [(p[0] + 10, p[1]) for p in SQUARE]
        polys = [
            {"coords": SQUARE, "base": 0.0, "height": 3.0},
            {"coords": far_square, "base": 0.0, "height": 3.0},
        ]
        self.assertTrue(
            segment_blocked_by_polygons((11, 0, 1), (15, 0, 1), polys)
        )

    def test_degenerate_polygon_ignored(self):
        self.assertFalse(
            segment_blocked_by_polygon(
                (0, 0, 1), (5, 0, 1), [(0, 0), (1, 0)], 0.0, 3.0
            )
        )


class OccludedSensorTest(unittest.TestCase):
    """End-to-end test: sensors honour the polygon store on the graph engine."""

    def setUp(self) -> None:
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={'level': 'CRITICAL'},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        # Two nodes facing each other across a wall.
        self.ctx.graph.graph.add_node({'id': 0, 'x': 0.0, 'y': 0.0})
        self.ctx.graph.graph.add_node({'id': 1, 'x': 10.0, 'y': 0.0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 10.0, 'y': 10.0})
        self.ctx.graph.graph.add_edge({'id': 0, 'source': 0, 'target': 1, 'length': 10})
        self.ctx.graph.graph.add_edge({'id': 1, 'source': 0, 'target': 2, 'length': 14.14})

    def tearDown(self) -> None:
        self.ctx.terminate()

    def _add_blocking_wall(self):
        # A thin tall wall between (0, 0) and (10, 0).
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

    def test_occluded_range_drops_blocked_node(self):
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
        # Node 1 is hidden behind the wall, node 2 is off to the side.
        self.assertNotIn(1, occluded.data['nodes'])
        self.assertIn(2, occluded.data['nodes'])

    def test_occluded_no_polygons_matches_baseline(self):
        sensor = self.ctx.sensor.create_sensor(
            'no_polys', gamms.typing.SensorType.OCCLUDED_MAP, sensor_range=20.0,
        )
        sensor.sense(0)
        # Without polygons the occluded sensor must behave exactly like the
        # plain range sensor.
        self.assertIn(1, sensor.data['nodes'])
        self.assertIn(2, sensor.data['nodes'])

    def test_occluded_agent_sensor_drops_blocked_agents(self):
        self._add_blocking_wall()
        self.ctx.agent.create_agent('hidden', start_node_id=1)
        self.ctx.agent.create_agent('visible', start_node_id=2)

        sensor = self.ctx.sensor.create_sensor(
            'occluded_agent',
            gamms.typing.SensorType.OCCLUDED_AGENT,
            sensor_range=30.0,
        )
        sensor.sense(0)
        self.assertNotIn('hidden', sensor.data)
        self.assertIn('visible', sensor.data)

    def test_occluded_aerial_sees_through_when_above_buildings(self):
        # Drone flying high should still see the node hidden behind the wall.
        self._add_blocking_wall()
        aerial = self.ctx.agent.create_agent(
            name='drone',
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        aerial.position = (0.0, 0.0, 20.0)

        sensor = self.ctx.sensor.create_sensor(
            'aerial_occluded',
            gamms.typing.SensorType.OCCLUDED_AERIAL,
            sensor_range=50.0,
            fov=math.pi,
        )
        sensor.set_owner(aerial.name)
        sensor.sense(0)
        # The drone is high above so its rays come down at a steep angle and
        # avoid the wall; node 1 should still be visible.
        self.assertIn(1, sensor.data['nodes'])

    def test_occluded_range_ignores_polygons_outside_range(self):
        # A polygon far outside the sensor range must not affect the result.
        self._add_blocking_wall()  # the relevant occluder near the agent
        # An unrelated polygon way off to the side, well outside any sensor range.
        far_coords = [(500, 500), (510, 500), (510, 510), (500, 510)]
        for i in range(4):
            p1, p2 = far_coords[i], far_coords[(i + 1) % 4]
            self.ctx.graph.add_obstacle_face(
                99 * 10000 + i,
                tr=(p2[0], p2[1], 20.0),
                tl=(p1[0], p1[1], 20.0),
                br=(p2[0], p2[1], 0.0),
                bl=(p1[0], p1[1], 0.0),
                type=0,
            )
        sensor = self.ctx.sensor.create_sensor(
            'occluded_filtered',
            gamms.typing.SensorType.OCCLUDED_MAP,
            sensor_range=20.0,
        )
        sensor.sense(0)
        # Occlusion behaviour must match the wall-only case: node 1 hidden,
        # node 2 visible. The far polygon doesn't sneak in.
        self.assertNotIn(1, sensor.data['nodes'])
        self.assertIn(2, sensor.data['nodes'])

    def test_occluded_aerial_loses_node_when_low(self):
        self._add_blocking_wall()
        aerial = self.ctx.agent.create_agent(
            name='drone',
            type=gamms.typing.agent_engine.AgentType.AERIAL,
            start_node_id=0,
            speed=5.0,
        )
        # Drone hovering low, looking horizontally - wall should occlude.
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
    for cls in (OcclusionGeometryTest, OccludedSensorTest):
        s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return s


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
