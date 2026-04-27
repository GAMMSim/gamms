import os
import tempfile
import unittest

import gamms
from gamms.MemoryEngine import MemoryEngine, MemoryStore, SqliteStore, PathLike
from gamms.typing.memory_engine import StoreType


class MemoryStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = MemoryEngine()

    def tearDown(self) -> None:
        self.engine.terminate()

    def test_create_and_get_store(self):
        store = self.engine.create_store(StoreType.MEMORY, 'cars')
        self.assertEqual(store.name, 'cars')
        self.assertEqual(store.store_type, StoreType.MEMORY)
        self.assertIs(store, self.engine.get_store('cars'))
        self.assertIn('cars', self.engine.list_stores())

    def test_duplicate_store_raises(self):
        self.engine.create_store(StoreType.MEMORY, 'a')
        with self.assertRaises(ValueError):
            self.engine.create_store(StoreType.MEMORY, 'a')

    def test_unknown_store_raises(self):
        with self.assertRaises(KeyError):
            self.engine.get_store('does-not-exist')

    def test_map_lifecycle(self):
        store = self.engine.create_store(StoreType.MEMORY, 's')
        self.assertFalse(store.has_map('m'))
        store.create_map('m', value_type=dict)
        self.assertTrue(store.has_map('m'))
        self.assertIn('m', store.list_maps())

        store.insert_data('m', 1, {'name': 'foo'})
        self.assertTrue(store.has_data('m', 1))
        self.assertEqual(store.get_data('m', 1)['name'], 'foo')

        store.update_data('m', 1, {'name': 'bar'})
        self.assertEqual(store.get_data('m', 1)['name'], 'bar')
        self.assertEqual(list(store.keys('m')), [1])

        store.delete_data('m', 1)
        self.assertFalse(store.has_data('m', 1))
        with self.assertRaises(KeyError):
            store.get_data('m', 1)
        with self.assertRaises(KeyError):
            store.delete_data('m', 1)

    def test_duplicate_key_raises(self):
        store = self.engine.create_store(StoreType.MEMORY, 's')
        store.create_map('m')
        store.insert_data('m', 'k', 1)
        with self.assertRaises(ValueError):
            store.insert_data('m', 'k', 2)

    def test_create_duplicate_map_raises(self):
        store = self.engine.create_store(StoreType.MEMORY, 's')
        store.create_map('m')
        with self.assertRaises(ValueError):
            store.create_map('m')

    def test_unknown_map_raises(self):
        store = self.engine.create_store(StoreType.MEMORY, 's')
        with self.assertRaises(KeyError):
            store.insert_data('nope', 1, 1)
        with self.assertRaises(KeyError):
            store.get_data('nope', 1)
        with self.assertRaises(KeyError):
            list(store.keys('nope'))


class SqliteStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = PathLike(os.path.join(self.tmpdir.name, 'data.db'))
        self.engine = MemoryEngine()
        self.store = self.engine.create_store(StoreType.DATABASE, 'sqlite_store', self.path)

    def tearDown(self) -> None:
        self.engine.terminate()
        self.tmpdir.cleanup()

    def test_persisted_round_trip(self):
        self.store.create_map('items', value_type=dict)
        self.store.insert_data('items', 'k1', {'value': 42})
        self.store.insert_data('items', 'k2', {'value': 7})
        self.assertEqual(set(self.store.keys('items')), {'k1', 'k2'})
        self.assertEqual(self.store.get_data('items', 'k1'), {'value': 42})

        # Reopen using load_store; the same data should reappear.
        engine2 = MemoryEngine()
        store2 = engine2.load_store(StoreType.DATABASE, 'sqlite_store', self.path)
        self.assertTrue(store2.has_map('items'))
        self.assertEqual(store2.get_data('items', 'k1'), {'value': 42})
        self.assertEqual(store2.get_data('items', 'k2'), {'value': 7})
        engine2.terminate()

    def test_database_requires_path(self):
        with self.assertRaises(ValueError):
            self.engine.create_store(StoreType.DATABASE, 'no_path')


class PolygonStoreOnGraphEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={'level': 'CRITICAL'},
            graph_engine=gamms.graph.Engine.MEMORY,
        )

    def tearDown(self) -> None:
        self.ctx.terminate()

    def test_add_get_remove_polygon(self):
        coords = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.ctx.graph.add_polygon(0, coords)
        self.assertEqual(list(self.ctx.graph.get_polygons()), [0])
        record = self.ctx.graph.get_polygon(0)
        self.assertEqual(record['id'], 0)
        # Default 2-storey building height (~6 m).
        self.assertEqual(record['height'], 6.0)
        self.assertEqual(record['category'], 'building')

        self.ctx.graph.add_polygon(1, coords, height=12.5, category='foliage')
        self.assertEqual(set(self.ctx.graph.get_polygons()), {0, 1})
        self.assertEqual(self.ctx.graph.get_polygon(1)['height'], 12.5)
        self.assertEqual(self.ctx.graph.get_polygon(1)['category'], 'foliage')

        self.ctx.graph.remove_polygon(0)
        self.assertEqual(list(self.ctx.graph.get_polygons()), [1])

    def test_polygon_validation(self):
        with self.assertRaises(ValueError):
            self.ctx.graph.add_polygon(0, [(0, 0), (1, 1)])
        # Closing vertex is dropped; the polygon below has only two distinct
        # points and must be rejected.
        with self.assertRaises(ValueError):
            self.ctx.graph.add_polygon(0, [(0, 0), (1, 1), (0, 0)])
        with self.assertRaises(ValueError):
            self.ctx.graph.add_polygon(0, [(0, 0), (1, 0), (1, 1)], height=0)

    def test_internal_context_is_initialised(self):
        self.assertIsNotNone(self.ctx.ictx)
        self.assertIsNotNone(self.ctx.ictx.memory)


def suite():
    s = unittest.TestSuite()
    for cls in (MemoryStoreTest, SqliteStoreTest, PolygonStoreOnGraphEngineTest):
        s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return s


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
