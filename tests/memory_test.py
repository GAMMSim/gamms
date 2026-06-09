import unittest

import gamms
from gamms.MemoryEngine.store import PathLike


class StoreTestBase(unittest.TestCase):
    def test_create_delete_map(self):
        self.store.create_map('m', {'id': int, 'name': str}, 'id')
        self.assertIn('m', self.store.list_maps())

        with self.assertRaises(ValueError):
            self.store.create_map('m', {'id': int, 'name': str}, 'id')
        
        self.store.delete_map('m')

        with self.assertRaises(IndexError):
            self.store.create_map('m', {'id': int, 'name': tuple}, 'name')
        
        with self.assertRaises(IndexError):
            self.store.create_map('m', {'id': int, 'name': tuple}, 'tag')
        
        with self.assertRaises(KeyError):
            self.store.delete_map('m')
    
    def test_insert_get_update_data(self):
        self.store.create_map('m', {'id': int, 'name': str}, 'id')
        self.store.insert_data('m', {'id': 1, 'name': 'foo'})
        data = self.store.get_data('m', 1)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], 'foo')

        with self.assertRaises(IndexError):
            self.store.insert_data('q', {'id': 1, 'name': 'bar'})

        with self.assertRaises(KeyError):
            self.store.insert_data('m', {'id': 1, 'name': 'bar'})
                
        with self.assertRaises(ValueError):
            self.store.insert_data('m', {'id': 2, 'tag': 'baz'})
        
        with self.assertRaises(IndexError):
            self.store.get_data('q', 1)
        
        with self.assertRaises(KeyError):
            self.store.get_data('m', 999)
        
        with self.assertRaises(IndexError):
            self.store.update_data('q', {'id': 1, 'name': 'bar'})
        
        with self.assertRaises(KeyError):
            self.store.update_data('m', {'id': 3, 'name': 'baz'})
                        
        self.store.update_data('m', {'id': 1, 'name': 'qux'})
        data = self.store.get_data('m', 1)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], 'qux')

    def test_delete_data(self):
        self.store.create_map('m', {'id': int, 'name': str}, 'id')
        self.store.insert_data('m', {'id': 1, 'name': 'foo'})
        self.store.delete_data('m', 1)

        with self.assertRaises(IndexError):
            self.store.delete_data('q', 1)
        
        with self.assertRaises(KeyError):
            self.store.delete_data('m', 1)
        
    
    def test_list_maps(self):
        self.store.create_map('m1', {'id': int}, 'id')
        self.store.create_map('m2', {'id': int}, 'id')
        maps = self.store.list_maps()
        self.assertIn('m1', maps)
        self.assertIn('m2', maps)
    
    def test_query_keys(self):
        self.store.create_map('m', {'id': int, 'name': str}, 'id')
        self.store.insert_data('m', {'id': 1, 'name': 'foo'})
        self.store.insert_data('m', {'id': 2, 'name': 'bar'})
        keys = list(self.store.query_keys('m'))
        self.assertIn(1, keys)
        self.assertIn(2, keys)

        with self.assertRaises(IndexError):
            list(self.store.query_keys('q'))
    
    def tearDown(self) -> None:
        return self.ctx.terminate()

class MemoryStoreTest(StoreTestBase):
    def setUp(self):
        self.ctx = gamms.create_context(logger_config={'level': 'ERROR'})
        self.store = self.ctx.ictx.memory.create_store(gamms.typing.StoreType.MEMORY, 'test_store')


class SqliteStoreTest(StoreTestBase):
    def setUp(self):
        self.ctx = gamms.create_context(logger_config={'level': 'ERROR'})
        self.store = self.ctx.ictx.memory.create_store(gamms.typing.StoreType.DATABASE, 'test_store', path=PathLike(':memory:'))

class MemoryEngineTestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = gamms.create_context(logger_config={'level': 'ERROR'})
    
    def test_create_get_list_store(self):
        store = self.ctx.ictx.memory.create_store(gamms.typing.StoreType.MEMORY, 'mem_store')
        self.assertIsInstance(store, gamms.typing.IStore)

        with self.assertRaises(ValueError):
            self.ctx.ictx.memory.create_store(gamms.typing.StoreType.MEMORY, 'mem_store')
        
        store2 = self.ctx.ictx.memory.create_store(gamms.typing.StoreType.DATABASE, 'sqlite_store', path=PathLike(':memory:'))
        self.assertIsInstance(store2, gamms.typing.IStore)

        with self.assertRaises(ValueError):
            self.ctx.ictx.memory.create_store(gamms.typing.StoreType.DATABASE, 'sqlite_store', path=PathLike(':memory:'))
        
        stores = list(self.ctx.ictx.memory.list_stores())
        self.assertIn('mem_store', stores)
        self.assertIn('sqlite_store', stores)

        with self.assertRaises(KeyError):
            self.ctx.ictx.memory.get_store('nonexistent_store')
        
        self.ctx.ictx.memory.get_store('mem_store')
        self.ctx.ictx.memory.get_store('sqlite_store')

def suite():
    s = unittest.TestSuite()
    for cls in (
        MemoryEngineTestSuite,
        MemoryStoreTest,
        SqliteStoreTest,
    ):
        s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return s


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
