from typing import Dict, List, Optional

from gamms.typing.memory_engine import IMemoryEngine, IPathLike, IStore, StoreType
from gamms.MemoryEngine.store import MemoryStore, PathLike, SqliteStore


class MemoryEngine(IMemoryEngine):
    """Default :class:`IMemoryEngine` implementation.

    The engine owns a registry of stores. Stores are created on demand and
    each store carries its own backend (memory, sqlite, ...).
    """

    def __init__(self) -> None:
        self._stores: Dict[str, IStore] = {}

    @staticmethod
    def _build_store(
        store_type: StoreType,
        name: str,
        path: Optional[IPathLike],
    ) -> IStore:
        if store_type == StoreType.MEMORY:
            return MemoryStore(name, path)  # type: ignore[arg-type]
        if store_type == StoreType.DATABASE:
            if path is None:
                raise ValueError("DATABASE store requires a path.")
            return SqliteStore(name, path)  # type: ignore[arg-type]
        if store_type == StoreType.FILESYSTEM:
            # Filesystem stores are not used for structured data and are
            # intentionally limited to whole-store snapshots via MemoryStore.
            return MemoryStore(name, path)  # type: ignore[arg-type]
        raise ValueError(f"Unsupported store type: {store_type}")

    def create_store(
        self,
        store_type: StoreType,
        name: str,
        path: Optional[IPathLike] = None,
    ) -> IStore:
        if name in self._stores:
            raise ValueError(f"Store with name '{name}' already exists.")
        store = self._build_store(store_type, name, path)
        self._stores[name] = store
        return store

    def get_store(self, name: str) -> IStore:
        if name not in self._stores:
            raise KeyError(f"Store with name '{name}' does not exist.")
        return self._stores[name]

    def list_stores(self) -> List[str]:
        return list(self._stores.keys())

    def load_store(
        self,
        store_type: StoreType,
        name: str,
        path: IPathLike,
    ) -> IStore:
        if name in self._stores:
            return self._stores[name]
        store = self._build_store(store_type, name, path)
        store.load()
        self._stores[name] = store
        return store

    def save_store(self, name: str, path: Optional[IPathLike] = None) -> None:
        store = self.get_store(name)
        if path is not None and hasattr(store, "_path"):
            # Allow callers to redirect the snapshot location.
            store._path = path  # type: ignore[attr-defined]
        store.save()

    def terminate(self) -> None:
        for store in self._stores.values():
            close = getattr(store, "close", None)
            if callable(close):
                close()
        self._stores.clear()


__all__ = ["MemoryEngine", "MemoryStore", "SqliteStore", "PathLike"]
