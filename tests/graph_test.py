import unittest
import gamms
from shapely.geometry import LineString
import networkx as nx

class GraphTest(unittest.TestCase):
    def test_node_add_get(self):
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        node = self.ctx.graph.graph.get_node(1)
        self.assertIsNotNone(node)
        self.assertEqual(node.id, 1)
        self.assertEqual(node.x, 0)
        self.assertEqual(node.y, 0)

        with self.assertRaises(KeyError):
            self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})

        with self.assertRaises(ValueError):
            self.ctx.graph.graph.add_node({'id': 0,})
        
        with self.assertRaises(ValueError):
            self.ctx.graph.graph.add_node({'x': 0, 'y': 0})
        
        with self.assertRaises(ValueError):
            self.ctx.graph.graph.add_node({'id': 0, 'x': 0})
        with self.assertRaises(ValueError):
            self.ctx.graph.graph.add_node({'id': 0, 'y': 0})
        
        with self.assertRaises(KeyError):
            self.ctx.graph.graph.get_node(2)
    
    def test_edge_add_get(self):
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 1, 'y': 1})
        self.ctx.graph.graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1})

        # Check if the edge was added correctly
        edge = self.ctx.graph.graph.get_edge(1)
        self.assertIsNotNone(edge)
        self.assertEqual(edge.id, 1)
        self.assertEqual(edge.source, 1)
        self.assertEqual(edge.target, 2)
        self.assertEqual(edge.length, 1)

        with self.assertRaises(KeyError):
            self.ctx.graph.graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1})

        with self.assertRaises(KeyError):
            self.ctx.graph.graph.add_edge({'id': 3, 'source': 1, 'target': 4, 'length': 1, 'linestring': LineString([(0, 0), (1, 1)])})

        with self.assertRaises(ValueError):
            self.ctx.graph.graph.add_edge({'id': 1, 'source': 1, 'target': 2})


        with self.assertRaises(KeyError):
            self.ctx.graph.graph.get_edge(2)
    
    def test_get_nodes(self):
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 1, 'y': 1})
        self.ctx.graph.graph.add_node({'id': 3, 'x': 2, 'y': 2})

        nodes = list(self.ctx.graph.graph.get_nodes())
        self.assertEqual(len(nodes), 3)
        self.assertIn(1, nodes)
        self.assertIn(2, nodes)
        self.assertIn(3, nodes)

        self.ctx.graph.graph.add_node({'id': 4, 'x': 100, 'y': 3})
        self.ctx.graph.graph.add_node({'id': 5, 'x': 101, 'y': 4})

        nodes = list(self.ctx.graph.graph.get_nodes(d=10, x=0, y=0))
        self.assertGreaterEqual(len(nodes), 3)
        self.assertIn(1, nodes)
        self.assertIn(2, nodes)
        self.assertIn(3, nodes)

        nodes = list(self.ctx.graph.graph.get_nodes(d=-1.0, x=0, y=0))
        self.assertEqual(len(nodes), 5)
        self.assertIn(1, nodes)
        self.assertIn(2, nodes)
        self.assertIn(3, nodes)
        self.assertIn(4, nodes)
        self.assertIn(5, nodes)
    
    def test_get_edges(self):
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 1, 'y': 1})
        self.ctx.graph.graph.add_node({'id': 3, 'x': 2, 'y': 2})

        self.ctx.graph.graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1})
        self.ctx.graph.graph.add_edge({'id': 2, 'source': 2, 'target': 3, 'length': 1})

        edges = list(self.ctx.graph.graph.get_edges())
        self.assertEqual(len(edges), 2)
        self.assertIn(1, edges)
        self.assertIn(2, edges)

        self.ctx.graph.graph.add_node({'id': 4, 'x': 100, 'y': 3})
        self.ctx.graph.graph.add_node({'id': 5, 'x': 101, 'y': 4})

        self.ctx.graph.graph.add_edge({'id': 3, 'source': 4, 'target': 5, 'length': 2})

        edges = list(self.ctx.graph.graph.get_edges(d=10, x=0, y=0))
        self.assertGreaterEqual(len(edges), 2)
        self.assertIn(1, edges)
        self.assertIn(2, edges)

        edges = list(self.ctx.graph.graph.get_edges(d=-1.0, x=0, y=0))
        self.assertEqual(len(edges), 3)
        self.assertIn(1, edges)
        self.assertIn(2, edges)
        self.assertIn(3, edges)
    
    def test_remove_node_edge(self):
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 1, 'y': 1})
        self.ctx.graph.graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1})

        # Remove edge
        self.ctx.graph.graph.remove_edge(1)
        with self.assertRaises(KeyError):
            self.ctx.graph.graph.get_edge(1)

        # Remove node
        self.ctx.graph.graph.remove_node(1)
        with self.assertRaises(KeyError):
            self.ctx.graph.graph.get_node(1)
        
        self.ctx.graph.graph.remove_node(2)
        
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 1, 'y': 1})
        self.ctx.graph.graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1})

        # Remove node
        self.ctx.graph.graph.remove_node(2)
        with self.assertRaises(KeyError):
            self.ctx.graph.graph.get_node(2)
        with self.assertRaises(KeyError):
            self.ctx.graph.graph.get_edge(1)
        
        # Check if the other node is still there
        node = self.ctx.graph.graph.get_node(1)
        self.assertIsNotNone(node)
    
    def test_update_node_edge(self):
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 1, 'y': 1})
        self.ctx.graph.graph.add_edge({'id': 1, 'source': 1, 'target': 2, 'length': 1})

        # Update node
        self.ctx.graph.graph.update_node({'id': 1, 'x': 10, 'y': 20})
        node = self.ctx.graph.graph.get_node(1)
        self.assertEqual(node.x, 10)
        self.assertEqual(node.y, 20)

        # Update edge
        self.ctx.graph.graph.update_edge({'id': 1, 'source': 1, 'target': 2, 'length': 2})
        edge = self.ctx.graph.graph.get_edge(1)
        self.assertEqual(edge.length, 2)
        
        with self.assertRaises(KeyError):
            self.ctx.graph.graph.update_node({'id': 3, 'x': 10, 'y': 20})
        
        with self.assertRaises(KeyError):
            self.ctx.graph.graph.update_edge({'id': 3, 'source': 1, 'target': 2, 'length': 2})
        
    def test_get_neighbors(self):
        self.ctx.graph.graph.add_node({'id': 1, 'x': 0, 'y': 0})
        self.ctx.graph.graph.add_node({'id': 2, 'x': 1, 'y': 1})
        self.ctx.graph.graph.add_node({'id': 3, 'x': 2, 'y': 2})
        self.ctx.graph.graph.add_edge({'id': 1, 'source': 2, 'target': 1, 'length': 1})
        self.ctx.graph.graph.add_edge({'id': 2, 'source': 2, 'target': 3, 'length': 1})

        neighbors = list(self.ctx.graph.graph.get_neighbors(2))
        self.assertEqual(len(neighbors), 2)
        self.assertIn(1, neighbors)
        self.assertIn(3, neighbors)
    
    def test_attach_network(self):
        with self.assertRaises(ValueError):
            self.ctx.graph.attach_networkx_graph(None)

        G = nx.DiGraph()
        G.add_node(1, x=0, y=0)
        G.add_node(2, x=1, y=1)
        G.add_edge(1, 2, id=1, length=1)
        self.ctx.graph.attach_networkx_graph(G)

        self.ctx.graph.graph.get_node(1)
        self.ctx.graph.graph.get_node(2)
        self.ctx.graph.graph.get_edge(1)

    def tearDown(self) -> None:
        self.ctx.terminate()


class MemoryGraphTest(GraphTest):
    def setUp(self):
        self.ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS, graph_engine=gamms.graph.Engine.MEMORY, logger_config={'level': 'ERROR'})

class SQLiteGraphTest(GraphTest):
    def setUp(self) -> None:
        self.ctx = gamms.create_context(vis_engine=gamms.visual.Engine.NO_VIS, graph_engine=gamms.graph.Engine.SQLITE, logger_config={'level': 'ERROR'})


def suite(cls):
    suite = unittest.TestSuite()
    suite.addTest(cls('test_node_add_get'))
    suite.addTest(cls('test_edge_add_get'))
    suite.addTest(cls('test_get_nodes'))
    suite.addTest(cls('test_get_edges'))
    suite.addTest(cls('test_remove_node_edge'))
    suite.addTest(cls('test_update_node_edge'))
    suite.addTest(cls('test_get_neighbors'))
    suite.addTest(cls('test_attach_network'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite(MemoryGraphTest))
    runner.run(suite(SQLiteGraphTest))