import os
import tempfile
import unittest

import gamms
from gamms.MemoryEngine import MemoryEngine, MemoryStore, PathLike, SqliteStore
from gamms.typing.memory_engine import StoreType


def _row_to_dict(row):
    return dict(row)


class _StoreContractMixin:
    """Shared assertions exercised against both store backends."""

    store_type: StoreType
    requires_path: bool

    def make_engine(self) -> MemoryEngine:
        return MemoryEngine()

    def make_path(self, name: str = 'data.db'):
        if not self.requires_path:
            return None
        return PathLike(os.path.join(self.tmpdir.name, name))

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.engine = self.make_engine()
        self.store = self.engine.create_store(self.store_type, 's', self.make_path())

    def tearDown(self) -> None:
        self.engine.terminate()
        self.tmpdir.cleanup()

    def test_store_meta(self):
        self.assertEqual(self.store.name(), 's')
        self.assertEqual(self.store.type, self.store_type)

    def test_basic_lifecycle(self):
        self.store.create_map('items', {'id': int, 'name': str}, 'id')
        self.assertIn('items', self.store.list_maps())

        self.store.insert_data('items', {'id': 1, 'name': 'foo'})
        self.assertEqual(_row_to_dict(self.store.get_data('items', 1)), {'id': 1, 'name': 'foo'})

        self.store.update_data('items', {'id': 1, 'name': 'bar'})
        self.assertEqual(_row_to_dict(self.store.get_data('items', 1))['name'], 'bar')
        self.assertEqual(list(self.store.query_keys('items')), [1])

        self.store.delete_data('items', 1)
        with self.assertRaises(IndexError):
            self.store.get_data('items', 1)
        with self.assertRaises(IndexError):
            self.store.delete_data('items', 1)

    def test_duplicate_key_raises(self):
        self.store.create_map('m', {'id': int, 'value': int}, 'id')
        self.store.insert_data('m', {'id': 1, 'value': 10})
        with self.assertRaises(ValueError):
            self.store.insert_data('m', {'id': 1, 'value': 20})

    def test_create_duplicate_map_raises(self):
        self.store.create_map('m', {'id': int}, 'id')
        with self.assertRaises(ValueError):
            self.store.create_map('m', {'id': int}, 'id')

    def test_unknown_map_raises(self):
        with self.assertRaises(KeyError):
            self.store.insert_data('nope', {'id': 1})
        with self.assertRaises(KeyError):
            self.store.get_data('nope', 1)
        with self.assertRaises(KeyError):
            list(self.store.query_keys('nope'))

    def test_delete_map(self):
        self.store.create_map('m', {'id': int}, 'id')
        self.store.delete_map('m')
        self.assertNotIn('m', self.store.list_maps())
        with self.assertRaises(KeyError):
            self.store.delete_map('m')

    def test_invalid_primary_key_raises(self):
        with self.assertRaises(IndexError):
            self.store.create_map('m', {'id': int}, 'pk')

    def test_unsupported_type_raises(self):
        class Custom:
            pass
        with self.assertRaises(TypeError):
            self.store.create_map('m', {'id': int, 'thing': Custom}, 'id')

    def test_collection_field_round_trip(self):
        self.store.create_map(
            'm',
            {'id': int, 'tags': list, 'meta': dict, 'pts': tuple},
            'id',
        )
        self.store.insert_data('m', {
            'id': 1,
            'tags': ['a', 'b'],
            'meta': {'k': 'v', 'n': 7},
            'pts': ((1.0, 2.0), (3.0, 4.0)),
        })
        row = _row_to_dict(self.store.get_data('m', 1))
        self.assertEqual(list(row['tags']), ['a', 'b'])
        self.assertEqual(row['meta'], {'k': 'v', 'n': 7})
        self.assertEqual(row['pts'], ((1.0, 2.0), (3.0, 4.0)))

    def test_bulk_insert_and_count(self):
        self.store.create_map('m', {'id': int, 'value': int}, 'id')
        self.store.bulk_insert('m', [
            {'id': 1, 'value': 1},
            {'id': 2, 'value': 2},
            {'id': 3, 'value': 3},
        ])
        self.assertEqual(self.store.count('m'), 3)
        self.assertEqual(set(self.store.query_keys('m')), {1, 2, 3})

    def test_create_index(self):
        self.store.create_map('m', {'id': int, 'x': float, 'y': float}, 'id')
        self.store.create_index('m', ('x', 'y'))


class MemoryStoreTest(_StoreContractMixin, unittest.TestCase):
    store_type = StoreType.MEMORY
    requires_path = False

    def test_get_map_backend_handle(self):
        self.store.create_map('m', {'id': int, 'name': str}, 'id')
        self.store.insert_data('m', {'id': 1, 'name': 'foo'})
        backing = self.store.get_map('m')
        self.assertEqual(backing[1], {'id': 1, 'name': 'foo'})


class SqliteStoreTest(_StoreContractMixin, unittest.TestCase):
    store_type = StoreType.DATABASE
    requires_path = True

    def test_database_requires_path(self):
        with self.assertRaises(ValueError):
            self.engine.create_store(StoreType.DATABASE, 'no_path')

    def test_persistent_round_trip(self):
        self.store.create_map('items', {'id': int, 'value': int}, 'id')
        self.store.insert_data('items', {'id': 1, 'value': 42})
        self.store.insert_data('items', {'id': 2, 'value': 7})
        self.store.flush()
        self.engine.terminate()

        # Reopen against the same path.
        engine2 = MemoryEngine()
        path = PathLike(os.path.join(self.tmpdir.name, 'data.db'))
        store2 = engine2.create_store(StoreType.DATABASE, 's2', path)
        self.assertIn('items', store2.list_maps())
        self.assertEqual(_row_to_dict(store2.get_data('items', 1)), {'id': 1, 'value': 42})
        self.assertEqual(_row_to_dict(store2.get_data('items', 2)), {'id': 2, 'value': 7})
        engine2.terminate()


class MemoryEngineRegistryTest(unittest.TestCase):
    def test_create_and_get_store(self):
        engine = MemoryEngine()
        try:
            store = engine.create_store(StoreType.MEMORY, 'cars')
            self.assertEqual(store.name(), 'cars')
            self.assertIs(store, engine.get_store('cars'))
            self.assertIn('cars', list(engine.list_stores()))
        finally:
            engine.terminate()

    def test_duplicate_store_raises(self):
        engine = MemoryEngine()
        try:
            engine.create_store(StoreType.MEMORY, 'a')
            with self.assertRaises(ValueError):
                engine.create_store(StoreType.MEMORY, 'a')
        finally:
            engine.terminate()

    def test_unknown_store_raises(self):
        engine = MemoryEngine()
        try:
            with self.assertRaises(KeyError):
                engine.get_store('does-not-exist')
        finally:
            engine.terminate()


class _PolygonStoreSharedTest(unittest.TestCase):
    """Polygon API works the same across both engine backends."""

    graph_engine_kind = None

    def setUp(self) -> None:
        if self.graph_engine_kind is None:
            self.skipTest("base class")
        self.ctx = gamms.create_context(
            vis_engine=gamms.visual.Engine.NO_VIS,
            logger_config={'level': 'CRITICAL'},
            graph_engine=self.graph_engine_kind,
        )

    def tearDown(self) -> None:
        self.ctx.terminate()

    def test_add_get_remove_polygon(self):
        coords = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.ctx.graph.add_polygon(0, coords)
        self.assertEqual(list(self.ctx.graph.get_polygons()), [0])
        record = self.ctx.graph.get_polygon(0)
        self.assertEqual(record['id'], 0)
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
        with self.assertRaises(ValueError):
            self.ctx.graph.add_polygon(0, [(0, 0), (1, 1), (0, 0)])
        with self.assertRaises(ValueError):
            self.ctx.graph.add_polygon(0, [(0, 0), (1, 0), (1, 1)], height=0)

    def test_polygon_range_query(self):
        # Two polygons: one near origin, one far away.
        self.ctx.graph.add_polygon(0, [(0, 0), (5, 0), (5, 5), (0, 5)])
        self.ctx.graph.add_polygon(1, [(200, 200), (210, 200), (210, 210), (200, 210)])
        all_ids = set(self.ctx.graph.get_polygons())
        self.assertEqual(all_ids, {0, 1})
        near = set(self.ctx.graph.get_polygons(20.0, 0.0, 0.0))
        self.assertEqual(near, {0})
        far = set(self.ctx.graph.get_polygons(20.0, 200.0, 200.0))
        self.assertEqual(far, {1})

    def test_internal_context_is_initialised(self):
        self.assertIsNotNone(self.ctx.ictx)
        self.assertIsNotNone(self.ctx.ictx.memory)


class PolygonStoreOnGraphMemoryTest(_PolygonStoreSharedTest):
    graph_engine_kind = gamms.graph.Engine.MEMORY


class PolygonStoreOnGraphSqliteTest(_PolygonStoreSharedTest):
    graph_engine_kind = gamms.graph.Engine.SQLITE


def suite():
    s = unittest.TestSuite()
    for cls in (
        MemoryStoreTest,
        SqliteStoreTest,
        MemoryEngineRegistryTest,
        PolygonStoreOnGraphMemoryTest,
        PolygonStoreOnGraphSqliteTest,
    ):
        s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return s


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
