import unittest
import gamms
from unittest.mock import patch, MagicMock

class TestContext(unittest.TestCase):
    def test_context_initialization(self):
        with patch('gamms.GraphEngine.graph_engine.GraphEngine') as MockGraph, \
             patch('gamms.VisualizationEngine.NoEngine') as MockNoVisual, \
             patch('gamms.VisualizationEngine.PygameVisualizationEngine') as MockPygame, \
             patch('gamms.AgentEngine.agent_engine.AgentEngine') as MockAgent, \
             patch('gamms.SensorEngine.sensor_engine.SensorEngine') as MockSensor, \
             patch('gamms.Recorder') as MockRecorder:
            
            ctx = gamms.create_context(
                graph_engine=gamms.graph.Engine.SQLITE,
                vis_engine=gamms.visual.Engine.NO_VIS,
                logger_config={'level': 'CRITICAL'}
            )


            self.assertIsInstance(ctx, gamms.Context)
            self.assertIsInstance(ctx.graph_engine, MagicMock)
            self.assertIsInstance(ctx.visual_engine, MagicMock)
            self.assertIsInstance(ctx.agent_engine, MagicMock)
            self.assertIsInstance(ctx.sensor_engine, MagicMock)
            self.assertIsInstance(ctx.recorder, MagicMock)
            self.assertEqual(ctx.logger.level, gamms.logger.CRITICAL)

            self.assertFalse(ctx.is_terminated())

            MockGraph.assert_called_once_with(ctx, engine=gamms.graph.Engine.SQLITE)
            MockNoVisual.assert_called_once_with(ctx)
            MockAgent.assert_called_once_with(ctx)
            MockSensor.assert_called_once_with(ctx)
            MockRecorder.assert_called_once_with(ctx)

            ctx.terminate()

            ctx = gamms.create_context(
                graph_engine=gamms.graph.Engine.MEMORY,
                vis_engine=gamms.visual.Engine.PYGAME,
                vis_kwargs={'width': 800, 'height': 600},
                logger_config={'level': 'DEBUG'}
            )

            self.assertIsInstance(ctx, gamms.Context)
            self.assertIsInstance(ctx.visual_engine, MagicMock)

            MockGraph.assert_called_with(ctx, engine=gamms.graph.Engine.MEMORY)
            MockPygame.assert_called_once_with(ctx, width=800, height=600)

            self.assertEqual(ctx.logger.level, gamms.logger.DEBUG)

            ctx.terminate()
    
    def test_context_termination(self):
        with patch('gamms.GraphEngine.graph_engine.GraphEngine') as MockGraph, \
             patch('gamms.VisualizationEngine.NoEngine') as MockNoVisual, \
             patch('gamms.AgentEngine.agent_engine.AgentEngine') as MockAgent, \
             patch('gamms.SensorEngine.sensor_engine.SensorEngine') as MockSensor, \
             patch('gamms.Recorder') as MockRecorder:
            
            ctx = gamms.create_context(
                graph_engine=gamms.graph.Engine.SQLITE,
                vis_engine=gamms.visual.Engine.NO_VIS,
                logger_config={'level': 'CRITICAL'}
            )

            # Emulate recording was started
            MockRecorder.record.return_value = True

            self.assertFalse(ctx.is_terminated())
            self.assertTrue(ctx._alive)
            ctx.terminate()

            self.assertTrue(ctx.is_terminated())
            self.assertFalse(ctx._alive)

            # Termination checked recorder status
            MockRecorder.return_value.record.assert_called_once()
            MockRecorder.return_value.stop.assert_called_once()

            # Check that all components were terminated
            MockGraph.return_value.terminate.assert_called_once()
            MockNoVisual.return_value.terminate.assert_called_once()
            MockAgent.return_value.terminate.assert_called_once()
            MockSensor.return_value.terminate.assert_called_once()

            # Check retermination does not raise an error
            ctx.terminate()



def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestContext('test_context_initialization'))
    suite.addTest(TestContext('test_context_termination'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())