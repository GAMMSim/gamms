import unittest
import gamms
import gamms.SensorEngine.sensor_engine
from unittest.mock import patch

import math

import gamms.typing

class SensorTest(unittest.TestCase):
    def setUp(self):
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={'level': 'CRITICAL'},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
        # Manually create a grid graph
        for i in range(25):
            self.ctx.graph.graph.add_node({'id': i, 'x': i % 5, 'y': i // 5})
        
        for i in range(25):
            for j in range(25):
                if i == j + 1 or i == j - 1 or i == j + 5 or i == j - 5:
                    self.ctx.graph.graph.add_edge(
                        {'id': i * 25 + j, 'source': i, 'target': j, 'length': 1}
                    )
    
    def test_neighbor_sensor(self):
        sensor = gamms.SensorEngine.sensor_engine.NeighborSensor(
            self.ctx, sensor_id='neighbor_sensor',
            sensor_type=gamms.SensorEngine.sensor_engine.SensorType.NEIGHBOR
        )

        self.assertEqual(None, sensor.update(None))

        sensor.sense(0)
        neighbors = list(sensor.data)
        self.assertEqual(len(neighbors), 3) # Node 0 has two neighbors: 1 and 5
        self.assertIn(1, neighbors)
        self.assertIn(5, neighbors)
        self.assertIn(0, neighbors)  # Node itself should also be included
    
    def test_map_sensor(self):
        sensor = gamms.SensorEngine.sensor_engine.MapSensor(
            self.ctx, sensor_id='map_sensor',
            sensor_type=gamms.SensorEngine.sensor_engine.SensorType.MAP,
            sensor_range=2.1,
            fov = 3.0,
            orientation=(-0.98, 0.02),
        )

        self.assertEqual(None, sensor.update(None))

        sensor.sense(12)
        data = sensor.data
        self.assertIsInstance(data, dict)
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        self.assertIn(11, data['nodes'])
        self.assertIn(10, data['nodes'])
        self.assertIn(6, data['nodes'])
        self.assertIn(16, data['nodes'])
        self.assertIn(12, data['nodes'])
        edge_pairs = [(edge.source, edge.target) for edge in data['edges']]
        self.assertIn((11, 12), edge_pairs)
        self.assertIn((12, 11), edge_pairs)
        self.assertIn((10, 11), edge_pairs)
        self.assertIn((11, 10), edge_pairs)
        self.assertIn((6, 11), edge_pairs)
        self.assertIn((11, 6), edge_pairs)
    
    def test_agent_sensor(self):
        sensor = gamms.SensorEngine.sensor_engine.AgentSensor(
            self.ctx, sensor_id='agent_sensor',
            sensor_type=gamms.SensorEngine.sensor_engine.SensorType.AGENT,
            sensor_range=2.1,
            fov=3.0,
            orientation=(-0.98, 0.02),
        )

        self.assertEqual(None, sensor.update(None))

        # Create agents at nodes 0 and 24
        self.ctx.agent.create_agent('agent_0', start_node_id=0)
        self.ctx.agent.create_agent('agent_1', start_node_id=24)

        sensor.sense(0)
        data = sensor.data
        self.assertIsInstance(data, dict)
        self.assertIn('agent_0', data)
        self.assertEqual(data['agent_0'], 0)
        self.assertNotIn('agent_1', data)

        sensor.sense(1)
        data = sensor.data
        self.assertIsInstance(data, dict)
        self.assertIn('agent_0', data)
        self.assertEqual(data['agent_0'], 0)
        self.assertNotIn('agent_1', data)

        sensor.sense(24)
        data = sensor.data
        self.assertIsInstance(data, dict)
        self.assertIn('agent_1', data)
        self.assertEqual(data['agent_1'], 24)
        self.assertNotIn('agent_0', data)

    def tearDown(self):
        self.ctx.terminate()


class SensorEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={'level': 'CRITICAL'},
            graph_engine=gamms.graph.Engine.MEMORY,
        )
    
    def test_add_get_sensor(self):
        with patch('gamms.SensorEngine.sensor_engine.ISensor') as MockSensor:
            MockSensor.return_value.sensor_id = 'test_sensor'

            sensor = MockSensor()

            with self.assertRaises(KeyError):
                self.ctx.sensor.get_sensor('test_sensor')

            self.assertEqual(sensor.sensor_id, 'test_sensor')
            self.ctx.sensor.add_sensor(sensor)

            retrieved_sensor = self.ctx.sensor.get_sensor('test_sensor')
            self.assertEqual(retrieved_sensor.sensor_id, 'test_sensor')

            with self.assertRaises(ValueError):
                self.ctx.sensor.add_sensor(sensor)
    
    def test_create_sensor(self):
        with self.assertRaises(ValueError):
            self.ctx.sensor.create_sensor(
                sensor_id='test_sensor',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.CUSTOM,
                sensor_range=10.0,
                fov=1.0,
                orientation=(1.0, 0.0)
            )
        
        with patch('gamms.SensorEngine.sensor_engine.NeighborSensor') as MockSensor:
            _ = self.ctx.sensor.create_sensor(
                sensor_id='test_sensor',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.NEIGHBOR
            )
            MockSensor.assert_called_once_with(
                self.ctx, 'test_sensor',
                gamms.SensorEngine.sensor_engine.SensorType.NEIGHBOR
            )
        
        with patch('gamms.SensorEngine.sensor_engine.MapSensor') as MockSensor:
            _ = self.ctx.sensor.create_sensor(
                sensor_id='test_map_sensor',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.MAP,
            )
            MockSensor.assert_called_once_with(
                self.ctx, 'test_map_sensor',
                gamms.SensorEngine.sensor_engine.SensorType.MAP,
                sensor_range=float('inf'), fov=2*math.pi
            )
        with patch('gamms.SensorEngine.sensor_engine.MapSensor') as MockSensor:
            _ = self.ctx.sensor.create_sensor(
                sensor_id='test_map_sensor_2',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.RANGE,
            )
            MockSensor.assert_called_once_with(
                self.ctx, 'test_map_sensor_2',
                gamms.SensorEngine.sensor_engine.SensorType.RANGE,
                sensor_range=30.0, fov=2*math.pi
            )
        with patch('gamms.SensorEngine.sensor_engine.MapSensor') as MockSensor:
            _ = self.ctx.sensor.create_sensor(
                sensor_id='test_map_sensor_2',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.RANGE,
            )
            MockSensor.assert_called_once_with(
                self.ctx, 'test_map_sensor_2',
                gamms.SensorEngine.sensor_engine.SensorType.RANGE,
                sensor_range=30.0, fov=2*math.pi
            )
        
        with patch('gamms.SensorEngine.sensor_engine.AgentSensor') as MockSensor:
            _ = self.ctx.sensor.create_sensor(
                sensor_id='test_agent_sensor',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.AGENT,
            )
            MockSensor.assert_called_once_with(
                self.ctx, 'test_agent_sensor',
                gamms.SensorEngine.sensor_engine.SensorType.AGENT,
                sensor_range=float('inf'), fov=2*math.pi,
            )
        
        with patch('gamms.SensorEngine.sensor_engine.AgentSensor') as MockSensor:
            _ = self.ctx.sensor.create_sensor(
                sensor_id='test_agent_sensor_2',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.AGENT_RANGE,
            )
            MockSensor.assert_called_once_with(
                self.ctx, 'test_agent_sensor_2',
                gamms.SensorEngine.sensor_engine.SensorType.AGENT_RANGE,
                sensor_range=30.0, fov=2*math.pi,
            )
        
        with patch('gamms.SensorEngine.sensor_engine.AgentSensor') as MockSensor:
            _ = self.ctx.sensor.create_sensor(
                sensor_id='test_agent_sensor_3',
                sensor_type=gamms.SensorEngine.sensor_engine.SensorType.AGENT_ARC,
            )
            MockSensor.assert_called_once_with(
                self.ctx, 'test_agent_sensor_3',
                gamms.SensorEngine.sensor_engine.SensorType.AGENT_ARC,
                sensor_range=30.0, fov=2*math.pi,
            )
    
    def test_custom_sensor(self):
        @self.ctx.sensor.custom(name='TEST')
        class CustomSensor(gamms.typing.ISensor):
            def __init__(self, sensor_id: str = 'custom_sensor', extra_param: int = 0):
                self._sensor_id = sensor_id
                # extra_param is just to demonstrate passing additional arguments.
                self.extra_param = extra_param
            
            @property
            def sensor_id(self) -> str:
                return self._sensor_id

            def sense(self, node_id: int) -> None:
                # Minimal implementation for testing.
                return
            
            def set_owner(self, owner: str) -> None:
                # Set the owner of the sensor.
                self.owner = owner
            
            @property
            def type(self) -> gamms.typing.SensorType:
                # Return the type of the sensor.
                return gamms.typing.SensorType.CUSTOM

            @property
            def data(self):
                return

            def update(self, data: dict) -> None:
                return
        
        custom = CustomSensor(extra_param=42)
        self.assertEqual(custom.type, gamms.typing.SensorType.TEST)

        with self.assertRaises(ValueError):
            self.ctx.sensor.custom(name='TEST')(CustomSensor)

    
    def tearDown(self) -> None:
        return self.ctx.terminate()

def suite():
    suite = unittest.TestSuite()
    suite.addTest(SensorTest('test_neighbor_sensor'))
    suite.addTest(SensorTest('test_map_sensor'))
    suite.addTest(SensorTest('test_agent_sensor'))
    suite.addTest(SensorEngineTest('test_add_get_sensor'))
    suite.addTest(SensorEngineTest('test_create_sensor'))
    suite.addTest(SensorEngineTest('test_custom_sensor'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())