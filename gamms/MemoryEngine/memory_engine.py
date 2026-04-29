from typing import Dict, Iterator, Optional

from gamms.typing.memory_engine import IMemoryEngine, IPathLike, IStore, StoreType
from gamms.MemoryEngine.store import MemoryStore, PathLike, SqliteStore


class MemoryEngine(IMemoryEngine):
    """Default :class:`IMemoryEngine` implementation.

    Owns a registry of stores, each of which carries its own backend.
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
            return MemoryStore(name, path)  # type: ignore[arg-type]
        raise ValueError(f"Unsupported store type: {store_type}")

    def create_store(
        self,
        store_type: StoreType,
        name: str,
        path: Optional[IPathLike] = None,
    ) -> IStore:
        if name in self._stores:
            raise ValueError(f"Store with name {name!r} already exists.")
        store = self._build_store(store_type, name, path)
        self._stores[name] = store
        return store

    def get_store(self, name: str) -> IStore:
        if name not in self._stores:
            raise KeyError(f"Store with name {name!r} does not exist.")
        return self._stores[name]

    def list_stores(self) -> Iterator[str]:
        return iter(list(self._stores.keys()))

    def terminate(self) -> None:
        for store in self._stores.values():
            close = getattr(store, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
        self._stores.clear()


__all__ = ["MemoryEngine", "MemoryStore", "SqliteStore", "PathLike"]
