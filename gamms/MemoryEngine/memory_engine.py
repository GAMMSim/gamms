from gamms.typing.memory_engine import IMemoryEngine
from typing import List, Dict
from gamms.MemoryEngine.store import TableStore
import sqlite3


class MemoryEngine(IMemoryEngine):
    def __init__(self, db_path: str = "engine.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.stores: Dict[str, TableStore] = {}
    
    def check_connection(self):
        try:
            self.conn.execute("SELECT 1")
        except sqlite3.Error as e:
            raise ConnectionError(f"Database connection error: {e}")
        return True

    def create_store(
        self,
        name: str,
        schema: Dict[str, str],
        primary_key: str
    ) -> TableStore:
        if name in self.stores:
            raise ValueError(f"Store '{name}' already exists")
        store = TableStore(self.conn, name, schema, primary_key)
        self.stores[name] = store
        return store

    def list_stores(self) -> List[str]:
        return list(self.stores.keys())

    def get_store(self, name: str) -> TableStore:
        if name not in self.stores:
            raise KeyError(f"Store '{name}' does not exist")
        return self.stores[name]

    def query_store(self, name: str, sql: str, params: List = None) -> List[Dict]:
        if name not in self.stores:
            raise KeyError(f"Store '{name}' does not exist")
        store = self.stores[name]
        return store.query(sql, params)
    
    def load_store(self, name):
        return 
    

    def terminate(self):
        self.conn.close()