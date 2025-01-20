from gamms.typing.memory_engine import IMemoryEngine, StoreType
from gamms.MemoryEngine.store import Store, PathLike
import os
from typing import Any, List

class MemoryEngine(IMemoryEngine):
    def __init__(self) -> None:
            self.stores = {}

    def create_store(self, store_type: StoreType, name: str, path: PathLike, obj: Any) -> 'Store':
        if name in self.stores:
            raise ValueError(f"Store with name '{name}' already exists.")
        
        new_store = Store(name, store_type, path)
        new_store.save(obj)
        self.stores[name] = new_store
        return new_store


    def list_store(self) -> List[str]:
        return list(self.stores.keys)

    def load_store(self, name: str) -> Any:
        if name not in self.stores:
            raise ValueError(f"Store with name '{name}' does not exist.")
        
        return self.stores[name].load()
    
    def terminate(self):
         return