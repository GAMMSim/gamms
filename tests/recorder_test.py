import unittest
import gamms
import io

class RecorderTest(unittest.TestCase):
    def setUp(self):
        self.ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS)
        # Manually create a grid graph
        for i in range(25):
            self.ctx.graph.graph.add_node({'id': i, 'x': i % 5, 'y': i // 5})
        
        for i in range(25):
            for j in range(25):
                if i == j + 1 or i == j - 1 or i == j + 5 or i == j - 5:
                    self.ctx.graph.graph.add_edge(
                        {'id': i * 25 + j, 'source': i, 'target': j, 'length': 1}
                    )

        # Create in memory file for recording
        self.record_fp = io.BytesIO()
        self.ctx.record.start(self.record_fp)

        # Create agent at node 0
        self.ctx.agent.create_agent('agent_0', start_node_id=0)
        # Create agent at node 24
        self.ctx.agent.create_agent('agent_1', start_node_id=24)

    def test_record(self):
        self.assertEqual(self.ctx.record.record(), True)
        # Create a recorded component
        @self.ctx.record.component(struct={'x': int, 'y': int})
        class TestComponent:
            def __init__(self):
                self.x = 0
                self.y = 0
        # Create a component
        comp = TestComponent(name='test')
        # Check if the component values are correct
        self.assertEqual(comp.x, 0)
        self.assertEqual(comp.y, 0)
        self.assertEqual(comp.name, 'test')
        comp.x = 1
        comp.y = 2

        # Check if the component values are correct
        self.assertEqual(comp.x, 1)
        self.assertEqual(comp.y, 2)

        # Move agent_0 to node 1
        self.ctx.agent.get_agent('agent_0').current_node_id = 1
        # Move agent_1 to node 23
        self.ctx.agent.get_agent('agent_1').current_node_id = 23
        # Simulate
        self.ctx.visual.simulate()
        # Check if the agents are at the correct nodes
        self.assertEqual(self.ctx.agent.get_agent('agent_0').current_node_id, 1)
        self.assertEqual(self.ctx.agent.get_agent('agent_1').current_node_id, 23)

        # Copy the recording to a new file
        self.record_fp.seek(0)
        self.fp_replay = io.BytesIO(self.record_fp.read())
        self.ctx.record.stop()

        # Remove agent_0 and agent_1
        self.ctx.agent.delete_agent('agent_0')
        self.ctx.agent.delete_agent('agent_1')
        # Check if the agents are removed
        self.assertRaises(KeyError, self.ctx.agent.get_agent, 'agent_0')
        self.assertRaises(KeyError, self.ctx.agent.get_agent, 'agent_1')

        # Remove the component
        self.ctx.record.delete_component('test')
        cls_key = (TestComponent.__module__, TestComponent.__qualname__)
        self.ctx.record.unregister_component(cls_key)
        # Check if the component is removed
        self.assertEqual(self.ctx.record.is_component_registered(cls_key), False)

        del TestComponent

        # Replay the recording
        try:
            for _ in self.ctx.record.replay(self.fp_replay):
                pass
        except ValueError:
            pass

        # Check if the agents are at the correct nodes
        self.assertEqual(self.ctx.agent.get_agent('agent_0').current_node_id, 1)
        self.assertEqual(self.ctx.agent.get_agent('agent_1').current_node_id, 23)

        # Check if the component is registered
        self.assertEqual(self.ctx.record.is_component_registered(cls_key), True)
        # Check if the component values are correct
        comp = self.ctx.record.get_component('test')
        self.assertEqual(comp.x, 1)
        self.assertEqual(comp.y, 2)

    
    def tearDown(self):
        self.ctx.terminate()

if __name__ == '__main__':
    unittest.main()