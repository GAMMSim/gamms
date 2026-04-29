import os
import pickle
import sqlite3
from typing import Any, Iterator, List, Optional, Type

from gamms.typing.memory_engine import IPathLike, IStore, StoreType


class PathLike(IPathLike):
    """Concrete :class:`IPathLike` implementation backed by an absolute path."""

    def __init__(self, path: str):
        if not path:
            raise ValueError("Path cannot be empty.")
        self.path = os.path.abspath(path)

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def as_str(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"PathLike({self.path!r})"


class MemoryStore(IStore):
    """In-memory store backed by Python dictionaries."""

    def __init__(self, name: str, path: Optional[PathLike] = None):
        self._name = name
        self._path = path
        self._maps: dict = {}
        self._types: dict = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def store_type(self) -> StoreType:
        return StoreType.MEMORY

    @property
    def path(self) -> Optional[PathLike]:
        return self._path

    def create_map(self, map_name: str, value_type: Optional[Type] = None) -> None:
        if map_name in self._maps:
            raise ValueError(f"Map '{map_name}' already exists in store '{self._name}'.")
        self._maps[map_name] = {}
        self._types[map_name] = value_type

    def has_map(self, map_name: str) -> bool:
        return map_name in self._maps

    def list_maps(self) -> List[str]:
        return list(self._maps.keys())

    def _require_map(self, map_name: str) -> dict:
        if map_name not in self._maps:
            raise KeyError(f"Map '{map_name}' does not exist in store '{self._name}'.")
        return self._maps[map_name]

    def insert_data(self, map_name: str, key: Any, value: Any) -> None:
        m = self._require_map(map_name)
        if key in m:
            raise ValueError(f"Key {key!r} already exists in map '{map_name}'.")
        m[key] = value

    def get_data(self, map_name: str, key: Any) -> Any:
        m = self._require_map(map_name)
        if key not in m:
            raise KeyError(f"Key {key!r} not found in map '{map_name}'.")
        return m[key]

    def update_data(self, map_name: str, key: Any, value: Any) -> None:
        m = self._require_map(map_name)
        if key not in m:
            raise KeyError(f"Key {key!r} not found in map '{map_name}'.")
        m[key] = value

    def delete_data(self, map_name: str, key: Any) -> None:
        m = self._require_map(map_name)
        if key not in m:
            raise KeyError(f"Key {key!r} not found in map '{map_name}'.")
        del m[key]

    def has_data(self, map_name: str, key: Any) -> bool:
        return map_name in self._maps and key in self._maps[map_name]

    def keys(self, map_name: str) -> Iterator[Any]:
        return iter(self._require_map(map_name).keys())

    def items(self, map_name: str) -> Iterator[Any]:
        return iter(self._require_map(map_name).items())

    def save(self, obj: Any = None) -> None:
        if obj is not None:
            # Allow callers to overwrite the store with an explicit dict snapshot.
            if not isinstance(obj, dict):
                raise ValueError("MemoryStore.save expects a dict snapshot or None.")
            self._maps = obj
            return
        if self._path is None:
            return
        os.makedirs(os.path.dirname(self._path.as_str()) or ".", exist_ok=True)
        with open(self._path.as_str(), "wb") as fh:
            pickle.dump({"maps": self._maps, "types": self._types}, fh)

    def load(self) -> Any:
        if self._path is None:
            return self._maps
        if not self._path.exists():
            raise FileNotFoundError(f"Store file '{self._path.as_str()}' does not exist.")
        with open(self._path.as_str(), "rb") as fh:
            data = pickle.load(fh)
        self._maps = data.get("maps", {})
        self._types = data.get("types", {})
        return self._maps

    def delete(self) -> None:
        self._maps.clear()
        self._types.clear()
        if self._path is not None and self._path.exists():
            os.remove(self._path.as_str())


class SqliteStore(IStore):
    """Store backed by a single SQLite database file.

    Each "map" is mapped to its own table with two columns: ``key`` (primary
    key, BLOB) and ``value`` (BLOB). Keys and values are pickled before being
    persisted, which keeps the API agnostic to value type at the cost of
    Python-only interoperability.
    """

    def __init__(self, name: str, path: PathLike):
        self._name = name
        self._path = path
        os.makedirs(os.path.dirname(self._path.as_str()) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self._path.as_str(), isolation_level=None)
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS _meta (map_name TEXT PRIMARY KEY, value_type TEXT)"
        )
        self._maps_cache = set()
        cursor = self._conn.execute("SELECT map_name FROM _meta")
        for row in cursor.fetchall():
            self._maps_cache.add(row[0])

    @property
    def name(self) -> str:
        return self._name

    @property
    def store_type(self) -> StoreType:
        return StoreType.DATABASE

    @property
    def path(self) -> PathLike:
        return self._path

    @staticmethod
    def _table(map_name: str) -> str:
        # Defensive: only allow safe table names.
        if not map_name.replace("_", "").isalnum():
            raise ValueError(f"Invalid map name: {map_name!r}")
        return f"map_{map_name}"

    def create_map(self, map_name: str, value_type: Optional[Type] = None) -> None:
        if map_name in self._maps_cache:
            raise ValueError(f"Map '{map_name}' already exists in store '{self._name}'.")
        table = self._table(map_name)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table} (key BLOB PRIMARY KEY, value BLOB)"
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO _meta (map_name, value_type) VALUES (?, ?)",
            (map_name, value_type.__name__ if value_type is not None else None),
        )
        self._maps_cache.add(map_name)

    def has_map(self, map_name: str) -> bool:
        return map_name in self._maps_cache

    def list_maps(self) -> List[str]:
        return list(self._maps_cache)

    def _require_map(self, map_name: str) -> str:
        if map_name not in self._maps_cache:
            raise KeyError(f"Map '{map_name}' does not exist in store '{self._name}'.")
        return self._table(map_name)

    def insert_data(self, map_name: str, key: Any, value: Any) -> None:
        table = self._require_map(map_name)
        kb, vb = pickle.dumps(key), pickle.dumps(value)
        try:
            self._conn.execute(f"INSERT INTO {table} (key, value) VALUES (?, ?)", (kb, vb))
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Key {key!r} already exists in map '{map_name}'.") from exc

    def get_data(self, map_name: str, key: Any) -> Any:
        table = self._require_map(map_name)
        cursor = self._conn.execute(f"SELECT value FROM {table} WHERE key = ?", (pickle.dumps(key),))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Key {key!r} not found in map '{map_name}'.")
        return pickle.loads(row[0])

    def update_data(self, map_name: str, key: Any, value: Any) -> None:
        table = self._require_map(map_name)
        kb = pickle.dumps(key)
        cursor = self._conn.execute(f"SELECT 1 FROM {table} WHERE key = ?", (kb,))
        if cursor.fetchone() is None:
            raise KeyError(f"Key {key!r} not found in map '{map_name}'.")
        self._conn.execute(
            f"UPDATE {table} SET value = ? WHERE key = ?", (pickle.dumps(value), kb)
        )

    def delete_data(self, map_name: str, key: Any) -> None:
        table = self._require_map(map_name)
        kb = pickle.dumps(key)
        cursor = self._conn.execute(f"SELECT 1 FROM {table} WHERE key = ?", (kb,))
        if cursor.fetchone() is None:
            raise KeyError(f"Key {key!r} not found in map '{map_name}'.")
        self._conn.execute(f"DELETE FROM {table} WHERE key = ?", (kb,))

    def has_data(self, map_name: str, key: Any) -> bool:
        if map_name not in self._maps_cache:
            return False
        table = self._table(map_name)
        cursor = self._conn.execute(f"SELECT 1 FROM {table} WHERE key = ?", (pickle.dumps(key),))
        return cursor.fetchone() is not None

    def keys(self, map_name: str) -> Iterator[Any]:
        table = self._require_map(map_name)
        cursor = self._conn.execute(f"SELECT key FROM {table}")
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield pickle.loads(row[0])

    def items(self, map_name: str) -> Iterator[Any]:
        table = self._require_map(map_name)
        cursor = self._conn.execute(f"SELECT key, value FROM {table}")
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield pickle.loads(row[0]), pickle.loads(row[1])

    def save(self, obj: Any = None) -> None:
        # SQLite stores autocommit on each statement; nothing to do.
        return

    def load(self) -> Any:
        # Load is a no-op once the connection is open. Return a snapshot for
        # callers that want the materialised contents.
        snapshot = {}
        for map_name in self._maps_cache:
            snapshot[map_name] = dict(self.items(map_name))
        return snapshot

    def delete(self) -> None:
        for map_name in list(self._maps_cache):
            self._conn.execute(f"DROP TABLE IF EXISTS {self._table(map_name)}")
        self._conn.execute("DELETE FROM _meta")
        self._maps_cache.clear()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass