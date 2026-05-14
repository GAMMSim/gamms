import os
import sqlite3
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple, Type

import cbor2

from gamms.typing.memory_engine import IPathLike, IStore, StoreType


_PRIMITIVE_TYPES = (int, float, str, bool, bytes)


class PathLike(IPathLike):
    """Local filesystem resource locator.

    ``IPathLike`` is intentionally generic so future implementations can
    locate remote resources (carrying scheme/host/port). This concrete class
    is the only one we ship today and treats ``path`` as an opaque string.
    """

    def __init__(self, path: str):
        if not path:
            raise ValueError("Path cannot be empty.")
        self.path = path

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def as_str(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"PathLike({self.path!r})"


def _validate_struct(struct: Dict[str, Type], primary_key: str) -> None:
    if not isinstance(struct, dict) or not struct:
        raise TypeError("struct must be a non-empty dict mapping field names to types.")
    for field, field_type in struct.items():
        if not isinstance(field, str) or not field:
            raise TypeError(f"Field name must be a non-empty string, got {field!r}.")
        if not isinstance(field_type, type):
            raise TypeError(f"Field {field!r} type must be a Python type, got {field_type!r}.")

    if primary_key not in struct:
        raise IndexError(f"Primary key {primary_key!r} not present in struct.")
    # Primary keys must be hashable and indexable; disallow unhashable collection types and non-scalar primitives.
    if struct[primary_key] not in _PRIMITIVE_TYPES:
        raise IndexError(
            f"Primary key {primary_key!r} must be an indexable scalar type, "
            f"got {struct[primary_key].__name__!r}."
        )

class MemoryStore(IStore):
    def __init__(self, name: str, path: Optional[PathLike] = None):
        self._name = name
        self._path = path
        self._maps: Dict[str, Dict[Any, Dict[str, Any]]] = {}
        self._schemas: Dict[str, Tuple[Dict[str, Type], str]] = {}

    def name(self) -> str:
        return self._name

    def path(self) -> Optional[IPathLike]:
        return self._path

    @property
    def type(self) -> StoreType:
        return StoreType.MEMORY

    def create_map(self, map_name: str, schema: Dict[str, Type], primary_key: str) -> None:
        if map_name in self._maps:
            raise ValueError(f"Map {map_name!r} already exists in store {self._name!r}.")
        _validate_struct(schema, primary_key)
        self._maps[map_name] = {}
        self._schemas[map_name] = (schema, primary_key)

    def delete_map(self, map_name: str) -> None:
        if map_name not in self._maps:
            raise KeyError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        del self._maps[map_name]
        del self._schemas[map_name]

    def list_maps(self) -> List[str]:
        return list(self._maps.keys())

    def _require_map(self, map_name: str) -> Tuple[Dict[Any, Dict[str, Any]], Dict[str, Type], str]:
        if map_name not in self._maps:
            raise IndexError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        schema, pk = self._schemas[map_name]
        return self._maps[map_name], schema, pk

    def insert_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        rows, schema, pk = self._require_map(map_name)
        for field in schema:
            if field not in struct:
                raise ValueError(f"Field {field!r} not declared in map schema.")
        if pk not in struct:
            raise ValueError(f"Primary key {pk!r} missing from struct.")
        key = struct[pk]
        if key in rows:
            raise KeyError(f"Key {key!r} already exists in map {map_name!r}.")
        rows[key] = struct

    def get_data(self, map_name: str, key: Any) -> Mapping[str, Any]:
        rows, schema, _ = self._require_map(map_name)
        if key not in rows:
            raise KeyError(f"Key {key!r} not found in map {map_name!r}.")
        row = rows[key]
        return row

    def update_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        rows, _, pk = self._require_map(map_name)
        if pk not in struct:
            raise ValueError(f"Primary key {pk!r} missing from struct.")
        key = struct[pk]
        if key not in rows:
            raise KeyError(f"Key {key!r} not found in map {map_name!r}.")
        rows[key].update(struct)

    def delete_data(self, map_name: str, key: Any) -> None:
        rows, _, _ = self._require_map(map_name)
        if key not in rows:
            raise KeyError(f"Key {key!r} not found in map {map_name!r}.")
        del rows[key]

    def query_keys(self, map_name: str) -> Iterator[Any]:
        rows, _, _ = self._require_map(map_name)
        return iter(rows.keys())

    def close(self) -> None:
        self._maps.clear()
        self._schemas.clear()



_PY_TO_SQL = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "INTEGER",
}


class LazyMapping(Mapping[str, Any]):
    """Helper for decoding SQL rows on demand according to a schema."""
    def __init__(self, schema: Dict[str, Type], data: Tuple[Tuple[str, Any], ...]):
        self._schema = schema
        self._data = dict(data)

    def __getitem__(self, key: str) -> Any:
        if key not in self._schema:
            raise KeyError(f"Field {key!r} not in map schema.")
        if key not in self._data:
            raise KeyError(f"Field {key!r} not found in data.")
        field_type = self._schema[key]
        raw = self._data[key]
        if raw is None:
            return None
        if field_type not in _PY_TO_SQL:
            decoded = field_type(cbor2.loads(raw))
            return decoded
        if field_type is bool:
            return bool(raw)
        return raw

    def __iter__(self) -> Iterator[str]:
        return iter(self._schema.keys())

    def __len__(self) -> int:
        return len(self._schema)

class SqliteStore(IStore):
    def __init__(self, name: str, path: PathLike):
        self._name = name
        self._path = path
        path_str = self._path.as_str()
        if path_str != ":memory:":
            parent = os.path.dirname(path_str)
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(path_str, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute("PRAGMA temp_store = MEMORY;")
        self._schemas: Dict[str, Tuple[Dict[str, Type], str]] = {}
        self._dirty = False

    def name(self) -> str:
        return self._name

    def path(self) -> PathLike:
        return self._path

    @property
    def type(self) -> StoreType:
        return StoreType.DATABASE

    def create_map(self, map_name: str, schema: Dict[str, Type], primary_key: str) -> None:
        if map_name in self._schemas:
            raise ValueError(f"Map {map_name!r} already exists in store {self._name!r}.")
        _validate_struct(schema, primary_key)
        col_defs: List[str] = []
        for field, field_type in schema.items():
            sql_type = _PY_TO_SQL.get(field_type, "BLOB")
            col_def = f"{field} {sql_type}"
            if field == primary_key:
                col_def += " PRIMARY KEY"
            col_defs.append(col_def)
        sql = f"CREATE TABLE {map_name} ({', '.join(col_defs)})"
        self._conn.execute(sql)
        self._schemas[map_name] = (schema, primary_key)

    def delete_map(self, map_name: str) -> None:
        if map_name not in self._schemas:
            raise IndexError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        self._conn.execute(f"DROP TABLE {map_name}")
        del self._schemas[map_name]

    def list_maps(self) -> List[str]:
        return list(self._schemas.keys())

    def _require_schema(self, map_name: str) -> Tuple[Dict[str, Type], str]:
        if map_name not in self._schemas:
            raise IndexError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        return self._schemas[map_name]

    def insert_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        schema, pk = self._require_schema(map_name)
        if pk not in struct:
            raise ValueError(f"Primary key {pk!r} missing from struct.")
        
        # All schema fields must be present in the struct
        values = []
        for key in schema:
            if key not in struct:
                raise ValueError(f"Field {key!r} missing from struct.")
            if schema[key] not in _PY_TO_SQL:
                encoded = cbor2.dumps(struct[key])
                values.append(encoded)
            elif schema[key] is bool:
                values.append(1 if struct[key] else 0)
            else:
                values.append(struct[key])

        cols = ", ".join(schema.keys())
        placeholders = ", ".join(["?"]*len(schema))
        try:
            self._conn.execute(
                f"INSERT INTO {map_name} ({cols}) VALUES ({placeholders})",
                tuple(values),
            )
        except sqlite3.IntegrityError as exc:
            raise KeyError(f"Key {struct[pk]!r} already exists in map {map_name!r}.") from exc
        self._dirty = True

    def get_data(self, map_name: str, key: Any) -> Mapping[str, Any]:
        schema, pk = self._require_schema(map_name)
        self.flush()
        cols = ", ".join(schema.keys())
        cursor = self._conn.execute(
            f"SELECT {cols} FROM {map_name} WHERE {pk} = ?",
            (key,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Key {key!r} not found in map {map_name!r}.")
        return LazyMapping(schema, tuple(zip(schema.keys(), row)))

    def update_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        schema, pk = self._require_schema(map_name)
        if pk not in struct:
            raise ValueError(f"Primary key {pk!r} missing from struct.")
        key = struct.pop(pk)
        # All struct fields must be present in the schema
        values = []
        assignments = []
        for field in struct:
            if field not in schema:
                raise ValueError(f"Field {field!r} not found in schema for map {map_name!r}.")
            if schema[field] not in _PY_TO_SQL:
                encoded = cbor2.dumps(struct[field])
                values.append(encoded)
            elif schema[field] is bool:
                values.append(1 if struct[field] else 0)
            else:
                values.append(struct[field])
            assignments.append(f"{field} = ?")
        
        assignments_str = ", ".join(assignments)
        try:
            self._conn.execute(
                f"UPDATE {map_name} SET {assignments_str} WHERE {pk} = ?",
                tuple(values + [key]),
            )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise KeyError(f"Key {key!r} not found in map {map_name!r}.") from exc
            else:
                raise ValueError(f"Unexpected error occurred while updating map {map_name!r}.") from exc
        self._dirty = True

    def delete_data(self, map_name: str, key: Any) -> None:
        schema, pk = self._require_schema(map_name)
        self.flush()
        try:
            self._conn.execute(
                f"DELETE FROM {map_name} WHERE {pk} = ?",
                (key,),
            )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise ValueError(f"Key {key!r} not found in map {map_name!r}.") from exc
            else:
                raise ValueError(f"Unexpected error occurred while deleting from map {map_name!r}.") from exc
        self._dirty = True

    def query_keys(self, map_name: str) -> Iterator[Any]:
        schema, pk = self._require_schema(map_name)
        self.flush()
        cursor = self._conn.execute(
            f"SELECT {pk} FROM {map_name}"
        )
        pk_type = schema[pk]
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield pk_type(row[0])

    # ---- generic extension methods --------------------------------------

    def connection(self) -> sqlite3.Connection:
        return self._conn

    def cursor(self) -> sqlite3.Cursor:
        return self._conn.cursor()

    def flush(self) -> None:
        if self._dirty:
            self._conn.commit()
            self._dirty = False

    def mark_dirty(self) -> None:
        """Mark pending writes that bypassed the IStore API.

        Consumers using ``connection()`` / ``cursor()`` directly should call
        this so subsequent reads ``flush()`` first.
        """
        self._dirty = True

    def close(self) -> None:
        self.flush()
        self._conn.close()