import unittest
import gamms

class AgentTest(unittest.TestCase):
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
        
        self.agent = gamms.agent.Agent(
            self.ctx,
            name='agent',
            start_node_id=0,
        )

        self.aerial = gamms.agent.AerialAgent(
            self.ctx,
            name='aerial',
            start_node_id=0,
            speed=2.0,
        )
    
    def test_common_properties(self):
        # Test name property
        self.assertEqual(self.agent.name, 'agent')
        self.assertEqual(self.aerial.name, 'aerial')

        # Test current_node_id property
        self.assertEqual(self.agent.current_node_id, 0)
        self.assertEqual(self.aerial.current_node_id, 0)

        # Test prev_node_id property
        self.assertEqual(self.agent.prev_node_id, 0)
        self.assertEqual(self.aerial.prev_node_id, 0)

        # Test node id setting
        self.agent.current_node_id = 4
        self.aerial.current_node_id = 10
        self.assertEqual(self.agent.current_node_id, 4)
        self.assertEqual(self.aerial.current_node_id, 10)
        self.assertEqual(self.agent.prev_node_id, 0)
        self.assertEqual(self.aerial.prev_node_id, 0)

        # Test type property
        self.assertEqual(self.agent.type, gamms.typing.agent_engine.AgentType.BASIC)
        self.assertEqual(self.aerial.type, gamms.typing.agent_engine.AgentType.AERIAL)

        # Test orientation property
        self.assertEqual(self.agent.orientation, (1.0, 0.0))
        self.assertEqual(self.aerial.orientation, (1.0, 0.0))

    
    def test_aerial_properties(self):
        # Test position property and current_node_id interaction
        self.assertEqual(self.aerial.position, (0.0, 0.0, 0.0))
        self.aerial.position = (1.0, 1.0, 1.0)
        self.assertEqual(self.aerial.position, (1.0, 1.0, 1.0))
        self.assertEqual(self.aerial.prev_position, (0.0, 0.0, 0.0))

        self.assertEqual(self.aerial.current_node_id, 6)
        self.assertEqual(self.aerial.prev_node_id, 0)

        # Test quaternion property
        self.assertEqual(self.aerial.quat, (1.0, 0.0, 0.0, 0.0))
        self.aerial.quat = (0.707, 0.0, 0.707, 0.0)
        quat = (0.707, 0.0, 0.707, 0.0)
        # Normalize quaternion
        norm = sum(q**2 for q in quat) ** 0.5
        quat = tuple(q / norm for q in quat)
        self.assertEqual(self.aerial.quat, quat)

    
class AgentEngineTest(unittest.TestCase):
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
    
    def test_engine(self):
        # create agent
        agent = self.ctx.agent.create_agent(
            name='agent',
            start_node_id=0,
        )

        self.assertEqual(agent.type, gamms.typing.agent_engine.AgentType.BASIC)

        # create aerial agent
        aerial = self.ctx.agent.create_agent(
            name='aerial',
            start_node_id=0,
            speed=2.0,
            type=gamms.typing.agent_engine.AgentType.AERIAL,
        )

        self.assertEqual(aerial.type, gamms.typing.agent_engine.AgentType.AERIAL)
        self.assertEqual(aerial.speed, 2.0)
        self.assertEqual(aerial.position, (0.0, 0.0, 0.0))
        self.assertEqual(aerial.quat, (1.0, 0.0, 0.0, 0.0))
        self.assertEqual(aerial.current_node_id, 0)
        self.assertEqual(aerial.prev_node_id, 0)

        # Test create iterator
        agents = list(self.ctx.agent.create_iter())
        self.assertEqual(len(agents), 2)
        self.assertIn(agent, agents)
        self.assertIn(aerial, agents)

        # Test delete agent
        self.ctx.agent.delete_agent('agent')
        
        # Test get agent
        with self.assertRaises(KeyError):
            self.ctx.agent.get_agent('agent')
        aerial_fetched = self.ctx.agent.get_agent('aerial')
        self.assertEqual(aerial, aerial_fetched)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AgentTest))
    suite.addTest(unittest.makeSuite(AgentEngineTest))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())