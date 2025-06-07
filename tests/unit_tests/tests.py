import unittest
import tempfile
import os
import shutil
import math
import networkx as nx
import pickle
import logging
from unittest.mock import Mock, patch, MagicMock
from shapely.geometry import LineString, Point

# Import GAMMS modules
import gamms

from gamms.typing import IContext
from gamms.typing.sensor_engine import SensorType
from gamms.context import Context
from gamms.MemoryEngine.memory_engine import MemoryEngine
from gamms.MemoryEngine.store import TableStore
from gamms.GraphEngine.graph_engine import Graph, GraphEngine
from gamms.AgentEngine.agent_engine import Agent, NoOpAgent, AgentEngine
from gamms.SensorEngine.sensor_engine import SensorEngine, NeighborSensor, MapSensor, AgentSensor
from gamms.Recorder.recorder import Recorder


class TestContext(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        # Clear any existing GAMMS_LOG_LEVEL env var
        self.original_log_level = os.environ.get('GAMMS_LOG_LEVEL')
        if 'GAMMS_LOG_LEVEL' in os.environ:
            del os.environ['GAMMS_LOG_LEVEL']
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if self.original_log_level:
            os.environ['GAMMS_LOG_LEVEL'] = self.original_log_level
            
    def test_create_context_with_no_vis(self):
        """Test creating context with NO_VIS engine"""
        # Mock the necessary modules
        with patch('gamms.MemoryEngine.memory_engine.MemoryEngine') as MockMemory, \
             patch('gamms.GraphEngine.graph_engine.GraphEngine') as MockGraph, \
             patch('gamms.AgentEngine.agent_engine.AgentEngine') as MockAgent, \
             patch('gamms.SensorEngine.sensor_engine.SensorEngine') as MockSensor, \
             patch('gamms.VisualizationEngine.NoEngine') as MockNoVis, \
             patch('gamms.Recorder') as MockRecorder:
            
            # Setup mock memory engine
            mock_memory_instance = Mock()
            mock_memory_instance.check_connection.return_value = True
            MockMemory.return_value = mock_memory_instance
            
            # Create context using the actual create_context function
            ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)
            ctx.record.start(path=os.path.join(self.temp_dir, "recording"))
            # Verify context is properly initialized
            self.assertIsInstance(ctx, Context)
            self.assertTrue(hasattr(ctx, 'agent_engine'))
            self.assertTrue(hasattr(ctx, 'sensor_engine'))
            self.assertTrue(hasattr(ctx, 'graph_engine'))
            self.assertTrue(hasattr(ctx, 'memory_engine'))
            self.assertTrue(hasattr(ctx, 'visual_engine'))
            self.assertTrue(hasattr(ctx, 'recorder'))
            self.assertTrue(hasattr(ctx, 'logger'))
            
            # Verify context is alive
            self.assertFalse(ctx.is_terminated())
            
            # Verify engines were created with context
            MockGraph.assert_called_once_with(ctx)
            MockAgent.assert_called_once_with(ctx)
            MockSensor.assert_called_once_with(ctx)
            MockNoVis.assert_called_once()
            MockRecorder.assert_called_once_with(ctx)
            
            # Verify memory connection was checked
            mock_memory_instance.check_connection.assert_called_once()
            
    def test_create_context_with_pygame(self):
        """Test creating context with PYGAME engine"""
        with patch('gamms.MemoryEngine.memory_engine.MemoryEngine') as MockMemory, \
             patch('gamms.GraphEngine.graph_engine.GraphEngine'), \
             patch('gamms.AgentEngine.agent_engine.AgentEngine'), \
             patch('gamms.SensorEngine.sensor_engine.SensorEngine'), \
             patch('gamms.VisualizationEngine.PygameVisualizationEngine') as MockPygame, \
             patch('gamms.Recorder.recorder.Recorder'):
            
            # Setup mock memory engine
            mock_memory_instance = Mock()
            mock_memory_instance.check_connection.return_value = True
            MockMemory.return_value = mock_memory_instance
            
            # Create context with pygame and custom kwargs
            vis_kwargs = {'width': 800, 'height': 600}
            ctx = gamms.create_context(
                vis_engine=gamms.visual.Engine.PYGAME,
                vis_kwargs=vis_kwargs
            )
            
            # Verify pygame engine was created with kwargs
            MockPygame.assert_called_once()
            call_args = MockPygame.call_args
            self.assertEqual(call_args[1], vis_kwargs)
            
    def test_create_context_memory_connection_failure(self):
        with patch('gamms.MemoryEngine.memory_engine.MemoryEngine') as MockMemory:
            # Setup mock memory engine to fail connection
            mock_memory_instance = Mock()
            mock_memory_instance.check_connection.return_value = False
            MockMemory.return_value = mock_memory_instance
            
            # Should raise ConnectionError
            with self.assertRaises(ConnectionError) as cm:
                gamms.create_context()
            
            self.assertIn("Database connection error", str(cm.exception))
            
    def test_create_context_with_logger_config(self):
        with patch('gamms.MemoryEngine.memory_engine.MemoryEngine') as MockMemory, \
             patch('gamms.GraphEngine.graph_engine.GraphEngine'), \
             patch('gamms.AgentEngine.agent_engine.AgentEngine'), \
             patch('gamms.SensorEngine.sensor_engine.SensorEngine'), \
             patch('gamms.VisualizationEngine.NoEngine'), \
             patch('gamms.Recorder.recorder.Recorder'), \
             patch('logging.basicConfig') as mock_basic_config:
            
            # Setup mock memory engine
            mock_memory_instance = Mock()
            mock_memory_instance.check_connection.return_value = True
            MockMemory.return_value = mock_memory_instance
            
            # Create context with custom logger config
            logger_config = {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
            ctx = gamms.create_context(logger_config=logger_config)
            
            # Verify basicConfig was called with our config + level
            mock_basic_config.assert_called_once()
            config_used = mock_basic_config.call_args[1]
            self.assertIn('format', config_used)
            self.assertIn('level', config_used)  # Level should be added
            
    def test_create_context_log_level_from_env(self):
        with patch('gamms.MemoryEngine.memory_engine.MemoryEngine') as MockMemory, \
             patch('gamms.GraphEngine.graph_engine.GraphEngine'), \
             patch('gamms.AgentEngine.agent_engine.AgentEngine'), \
             patch('gamms.SensorEngine.sensor_engine.SensorEngine'), \
             patch('gamms.VisualizationEngine.NoEngine'), \
             patch('gamms.Recorder.recorder.Recorder'):
            
            # Setup mock memory engine
            mock_memory_instance = Mock()
            mock_memory_instance.check_connection.return_value = True
            MockMemory.return_value = mock_memory_instance
            
            # Test different log levels
            test_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            
            for level in test_levels:
                os.environ['GAMMS_LOG_LEVEL'] = level
                ctx = gamms.create_context()
                # Just verify context was created successfully
                self.assertIsInstance(ctx, Context)
                
            # Test invalid level (should default to INFO)
            os.environ['GAMMS_LOG_LEVEL'] = 'INVALID'
            ctx = gamms.create_context()
            self.assertIsInstance(ctx, Context)
            
    def test_create_context_invalid_vis_engine(self):
        with patch('gamms.MemoryEngine.memory_engine.MemoryEngine') as MockMemory:
            # Setup mock memory engine
            mock_memory_instance = Mock()
            mock_memory_instance.check_connection.return_value = True
            MockMemory.return_value = mock_memory_instance
            
            # Create a fake engine type
            fake_engine = Mock()
            fake_engine.name = "INVALID_ENGINE"
            
            # Should raise NotImplementedError
            with self.assertRaises(NotImplementedError) as cm:
                gamms.create_context(vis_engine=fake_engine)
                
            self.assertIn("not implemented", str(cm.exception))
            
    def test_context_lifecycle(self):
        """Test context alive/terminated states"""
        ctx = Context()
        
        # Initially not alive
        self.assertTrue(ctx.is_terminated())
        
        # Set alive
        ctx.set_alive()
        self.assertFalse(ctx.is_terminated())
        
        # Create mock engines with terminate methods
        with patch('gamms.agent.AgentEngine') as MockAgent, \
             patch('gamms.sensor.SensorEngine') as MockSensor, \
             patch('gamms.graph.GraphEngine') as MockGraph, \
             patch('gamms.visual.NoEngine') as MockVisual, \
             patch('gamms.Recorder') as MockRecorder, \
             patch('gamms.memory.MemoryEngine') as MockMemory:
            
            ctx.agent_engine = MockAgent()
            ctx.sensor_engine = MockSensor()
            ctx.graph_engine = MockGraph()
            ctx.visual_engine = MockVisual()
            ctx.recorder = MockRecorder()
            ctx.memory_engine = MockMemory()
        # Terminate
        ctx.terminate()
        self.assertTrue(ctx.is_terminated())
        
        # Verify all engines were terminated
        ctx.agent_engine.terminate.assert_called_once()
        ctx.sensor_engine.terminate.assert_called_once()
        ctx.graph_engine.terminate.assert_called_once()
        ctx.visual_engine.terminate.assert_called_once()
        
    def test_context_properties(self):
        """Test that context properties return the correct engines"""
        # Create a context with mock engines
        ctx = Context()
        
        mock_agent = Mock()
        mock_sensor = Mock()
        mock_graph = Mock()
        mock_memory = Mock()
        mock_visual = Mock()
        mock_recorder = Mock()
        mock_logger = Mock()
        mock_ictx = Mock()
        
        ctx.agent_engine = mock_agent
        ctx.sensor_engine = mock_sensor
        ctx.graph_engine = mock_graph
        ctx.memory_engine = mock_memory
        ctx.visual_engine = mock_visual
        ctx.recorder = mock_recorder
        ctx._logger = mock_logger
        ctx.internal_context = mock_ictx
        
        # Test all property accessors
        self.assertEqual(ctx.agent, mock_agent)
        self.assertEqual(ctx.sensor, mock_sensor)
        self.assertEqual(ctx.graph, mock_graph)
        self.assertEqual(ctx.memory, mock_memory)
        self.assertEqual(ctx.visual, mock_visual)
        self.assertEqual(ctx.record, mock_recorder)
        self.assertEqual(ctx.logger, mock_logger)
        self.assertEqual(ctx.ictx, mock_ictx)



if __name__ == '__main__':
    unittest.main(verbosity=2)