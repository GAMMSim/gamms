import json
import os
import sqlite3
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Type

import cbor2

from gamms.typing.memory_engine import IPathLike, IStore, StoreType


_COLLECTION_TYPES = (list, tuple, dict, set)
_PRIMITIVE_TYPES = (int, float, str, bool, bytes, type(None))
_SUPPORTED_TYPES = _PRIMITIVE_TYPES + _COLLECTION_TYPES


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
        if field_type not in _SUPPORTED_TYPES:
            raise TypeError(
                f"Field {field!r} has unsupported type {field_type.__name__!r}."
            )
    if primary_key not in struct:
        raise IndexError(f"Primary key {primary_key!r} not present in struct.")
    if struct[primary_key] in _COLLECTION_TYPES:
        raise IndexError(
            f"Primary key {primary_key!r} must be an indexable scalar type, "
            f"got {struct[primary_key].__name__!r}."
        )


def _coerce_field(field: str, field_type: Type, value: Any) -> Any:
    if value is None and field_type is type(None):
        return None
    if isinstance(value, field_type):
        return value
    # Permit ints where floats are declared and vice-versa.
    if field_type is float and isinstance(value, (int, bool)):
        return float(value)
    if field_type is int and isinstance(value, bool):
        return int(value)
    raise ValueError(
        f"Field {field!r} expects {field_type.__name__}, got {type(value).__name__}."
    )


class MemoryStore(IStore):
    """In-memory ``IStore`` backed by Python dicts."""

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

    def create_map(self, map_name: str, struct: Dict[str, Type], primary_key: str) -> None:
        if map_name in self._maps:
            raise ValueError(f"Map {map_name!r} already exists in store {self._name!r}.")
        _validate_struct(struct, primary_key)
        self._maps[map_name] = {}
        self._schemas[map_name] = (dict(struct), primary_key)

    def delete_map(self, map_name: str) -> None:
        if map_name not in self._maps:
            raise KeyError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        del self._maps[map_name]
        del self._schemas[map_name]

    def list_maps(self) -> List[str]:
        return list(self._maps.keys())

    def _require_map(self, map_name: str) -> Tuple[Dict[Any, Dict[str, Any]], Dict[str, Type], str]:
        if map_name not in self._maps:
            raise KeyError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        struct, pk = self._schemas[map_name]
        return self._maps[map_name], struct, pk

    def _coerce_row(self, struct: Dict[str, Type], data: Dict[str, Any], partial: bool) -> Dict[str, Any]:
        row: Dict[str, Any] = {}
        for field, field_type in struct.items():
            if field in data:
                row[field] = _coerce_field(field, field_type, data[field])
            elif not partial:
                raise ValueError(f"Field {field!r} missing from struct.")
        for field in data:
            if field not in struct:
                raise ValueError(f"Field {field!r} not declared in map schema.")
        return row

    def insert_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        rows, schema, pk = self._require_map(map_name)
        if pk not in struct:
            raise IndexError(f"Primary key {pk!r} missing from struct.")
        row = self._coerce_row(schema, struct, partial=False)
        key = row[pk]
        if key in rows:
            raise ValueError(f"Key {key!r} already exists in map {map_name!r}.")
        rows[key] = row

    def get_data(self, map_name: str, key: Any) -> Tuple[Tuple[str, Any], ...]:
        rows, schema, _ = self._require_map(map_name)
        if key not in rows:
            raise IndexError(f"Key {key!r} not found in map {map_name!r}.")
        row = rows[key]
        return tuple((field, row[field]) for field in schema.keys())

    def update_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        rows, schema, pk = self._require_map(map_name)
        if pk not in struct:
            raise IndexError(f"Primary key {pk!r} missing from struct.")
        key = struct[pk]
        if key not in rows:
            raise IndexError(f"Key {key!r} not found in map {map_name!r}.")
        partial = self._coerce_row(schema, struct, partial=True)
        rows[key].update(partial)

    def delete_data(self, map_name: str, key: Any) -> None:
        rows, _, _ = self._require_map(map_name)
        if key not in rows:
            raise IndexError(f"Key {key!r} not found in map {map_name!r}.")
        del rows[key]

    def query_keys(self, map_name: str) -> Iterator[Any]:
        rows, _, _ = self._require_map(map_name)
        return iter(list(rows.keys()))

    # ---- generic extension methods --------------------------------------

    def create_index(self, map_name: str, fields: Sequence[str], name: Optional[str] = None) -> None:
        # In-memory linear scans don't benefit from indexes; documented as a hint.
        rows, schema, _ = self._require_map(map_name)
        for field in fields:
            if field not in schema:
                raise ValueError(f"Cannot index unknown field {field!r} on map {map_name!r}.")

    def bulk_insert(self, map_name: str, rows: Iterable[Dict[str, Any]]) -> None:
        for row in rows:
            self.insert_data(map_name, row)

    def count(self, map_name: str) -> int:
        rows, _, _ = self._require_map(map_name)
        return len(rows)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self._maps.clear()
        self._schemas.clear()

    def get_map(self, map_name: str) -> Dict[Any, Dict[str, Any]]:
        rows, _, _ = self._require_map(map_name)
        return rows


_PY_TO_SQL = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "INTEGER",
    bytes: "BLOB",
    list: "BLOB",
    tuple: "BLOB",
    dict: "BLOB",
    set: "BLOB",
    type(None): "BLOB",
}


def _is_collection_type(t: Type) -> bool:
    return t in _COLLECTION_TYPES


def _safe_identifier(name: str) -> str:
    if not name or not name.replace("_", "").isalnum():
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


class SqliteStore(IStore):
    """SQLite-backed ``IStore``. Schemas map onto tables ``map_<name>``."""

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
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS _meta (map_name TEXT PRIMARY KEY, schema TEXT, primary_key TEXT)"
        )
        self._schemas: Dict[str, Tuple[Dict[str, Type], str]] = {}
        for map_name, schema_json, pk in self._conn.execute(
            "SELECT map_name, schema, primary_key FROM _meta"
        ).fetchall():
            schema = self._decode_schema(schema_json)
            self._schemas[map_name] = (schema, pk)
        self._dirty = False

    def name(self) -> str:
        return self._name

    def path(self) -> PathLike:
        return self._path

    @property
    def type(self) -> StoreType:
        return StoreType.DATABASE

    @staticmethod
    def _encode_schema(struct: Dict[str, Type]) -> str:
        return json.dumps([(field, ftype.__name__) for field, ftype in struct.items()])

    @staticmethod
    def _decode_schema(blob: str) -> Dict[str, Type]:
        type_lookup = {t.__name__: t for t in _SUPPORTED_TYPES}
        type_lookup["NoneType"] = type(None)
        return {field: type_lookup[name] for field, name in json.loads(blob)}

    def table_name(self, map_name: str) -> str:
        if map_name not in self._schemas:
            raise KeyError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        return f"map_{_safe_identifier(map_name)}"

    def quote_field(self, field: str) -> str:
        return f'"{_safe_identifier(field)}"'

    def connection(self) -> sqlite3.Connection:
        return self._conn

    def cursor(self) -> sqlite3.Cursor:
        return self._conn.cursor()

    def create_map(self, map_name: str, struct: Dict[str, Type], primary_key: str) -> None:
        if map_name in self._schemas:
            raise ValueError(f"Map {map_name!r} already exists in store {self._name!r}.")
        _validate_struct(struct, primary_key)
        _safe_identifier(map_name)
        col_defs: List[str] = []
        for field, field_type in struct.items():
            sql_type = _PY_TO_SQL[field_type]
            col_def = f"{self.quote_field(field)} {sql_type}"
            if field == primary_key:
                col_def += " PRIMARY KEY"
            col_defs.append(col_def)
        sql = f"CREATE TABLE IF NOT EXISTS {self.table_name_hint(map_name)} ({', '.join(col_defs)})"
        self._conn.execute(sql)
        self._conn.execute(
            "INSERT OR REPLACE INTO _meta (map_name, schema, primary_key) VALUES (?, ?, ?)",
            (map_name, self._encode_schema(struct), primary_key),
        )
        self._schemas[map_name] = (dict(struct), primary_key)

    def table_name_hint(self, map_name: str) -> str:
        # Internal helper: builds the table name without consulting _schemas
        # (used during create_map before the schema is registered).
        return f"map_{_safe_identifier(map_name)}"

    def delete_map(self, map_name: str) -> None:
        if map_name not in self._schemas:
            raise KeyError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        self._conn.execute(f"DROP TABLE IF EXISTS {self.table_name(map_name)}")
        self._conn.execute("DELETE FROM _meta WHERE map_name = ?", (map_name,))
        del self._schemas[map_name]

    def list_maps(self) -> List[str]:
        return list(self._schemas.keys())

    def _require_schema(self, map_name: str) -> Tuple[Dict[str, Type], str]:
        if map_name not in self._schemas:
            raise KeyError(f"Map {map_name!r} does not exist in store {self._name!r}.")
        return self._schemas[map_name]

    def _encode_value(self, field_type: Type, value: Any) -> Any:
        if value is None:
            return None
        coerced = _coerce_field("<value>", field_type, value)
        if _is_collection_type(field_type):
            return cbor2.dumps(coerced if not isinstance(coerced, set) else list(coerced))
        if field_type is bool:
            return 1 if coerced else 0
        return coerced

    def _decode_value(self, field_type: Type, raw: Any) -> Any:
        if raw is None:
            return None
        if _is_collection_type(field_type):
            decoded = cbor2.loads(raw)
            if field_type is tuple:
                return _to_tuple_recursive(decoded)
            if field_type is set:
                return set(decoded)
            return decoded
        if field_type is bool:
            return bool(raw)
        return raw

    def _build_row_payload(
        self, schema: Dict[str, Type], data: Dict[str, Any], partial: bool
    ) -> Dict[str, Any]:
        for field in data:
            if field not in schema:
                raise ValueError(f"Field {field!r} not declared in map schema.")
        payload: Dict[str, Any] = {}
        for field, field_type in schema.items():
            if field in data:
                payload[field] = self._encode_value(field_type, data[field])
            elif not partial:
                raise ValueError(f"Field {field!r} missing from struct.")
        return payload

    def insert_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        schema, pk = self._require_schema(map_name)
        if pk not in struct:
            raise IndexError(f"Primary key {pk!r} missing from struct.")
        payload = self._build_row_payload(schema, struct, partial=False)
        cols = ", ".join(self.quote_field(f) for f in payload.keys())
        placeholders = ", ".join("?" for _ in payload)
        try:
            self._conn.execute(
                f"INSERT INTO {self.table_name(map_name)} ({cols}) VALUES ({placeholders})",
                tuple(payload.values()),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Key {struct[pk]!r} already exists in map {map_name!r}.") from exc
        self._dirty = True

    def get_data(self, map_name: str, key: Any) -> Tuple[Tuple[str, Any], ...]:
        schema, pk = self._require_schema(map_name)
        self.flush()
        cols = ", ".join(self.quote_field(f) for f in schema.keys())
        cursor = self._conn.execute(
            f"SELECT {cols} FROM {self.table_name(map_name)} WHERE {self.quote_field(pk)} = ?",
            (self._encode_value(schema[pk], key),),
        )
        row = cursor.fetchone()
        if row is None:
            raise IndexError(f"Key {key!r} not found in map {map_name!r}.")
        return tuple(
            (field, self._decode_value(schema[field], raw))
            for field, raw in zip(schema.keys(), row)
        )

    def update_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        schema, pk = self._require_schema(map_name)
        if pk not in struct:
            raise IndexError(f"Primary key {pk!r} missing from struct.")
        key = struct[pk]
        self.flush()
        cursor = self._conn.execute(
            f"SELECT 1 FROM {self.table_name(map_name)} WHERE {self.quote_field(pk)} = ?",
            (self._encode_value(schema[pk], key),),
        )
        if cursor.fetchone() is None:
            raise IndexError(f"Key {key!r} not found in map {map_name!r}.")
        payload = self._build_row_payload(schema, struct, partial=True)
        update_fields = [f for f in payload.keys() if f != pk]
        if not update_fields:
            return
        assignments = ", ".join(f"{self.quote_field(f)} = ?" for f in update_fields)
        params = tuple(payload[f] for f in update_fields) + (self._encode_value(schema[pk], key),)
        self._conn.execute(
            f"UPDATE {self.table_name(map_name)} SET {assignments} WHERE {self.quote_field(pk)} = ?",
            params,
        )
        self._dirty = True

    def delete_data(self, map_name: str, key: Any) -> None:
        schema, pk = self._require_schema(map_name)
        self.flush()
        cursor = self._conn.execute(
            f"SELECT 1 FROM {self.table_name(map_name)} WHERE {self.quote_field(pk)} = ?",
            (self._encode_value(schema[pk], key),),
        )
        if cursor.fetchone() is None:
            raise IndexError(f"Key {key!r} not found in map {map_name!r}.")
        self._conn.execute(
            f"DELETE FROM {self.table_name(map_name)} WHERE {self.quote_field(pk)} = ?",
            (self._encode_value(schema[pk], key),),
        )
        self._dirty = True

    def query_keys(self, map_name: str) -> Iterator[Any]:
        schema, pk = self._require_schema(map_name)
        self.flush()
        cursor = self._conn.execute(
            f"SELECT {self.quote_field(pk)} FROM {self.table_name(map_name)}"
        )
        pk_type = schema[pk]
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield self._decode_value(pk_type, row[0])

    # ---- generic extension methods --------------------------------------

    def create_index(self, map_name: str, fields: Sequence[str], name: Optional[str] = None) -> None:
        schema, _ = self._require_schema(map_name)
        for field in fields:
            if field not in schema:
                raise ValueError(f"Cannot index unknown field {field!r} on map {map_name!r}.")
        index_name = name or f"idx_{_safe_identifier(map_name)}_{'_'.join(_safe_identifier(f) for f in fields)}"
        cols = ", ".join(self.quote_field(f) for f in fields)
        self._conn.execute(
            f"CREATE INDEX IF NOT EXISTS {_safe_identifier(index_name)} ON {self.table_name(map_name)} ({cols})"
        )

    def bulk_insert(self, map_name: str, rows: Iterable[Dict[str, Any]]) -> None:
        schema, pk = self._require_schema(map_name)
        rows = list(rows)
        if not rows:
            return
        ordered_fields = list(schema.keys())
        cols = ", ".join(self.quote_field(f) for f in ordered_fields)
        placeholders = ", ".join("?" for _ in ordered_fields)
        params_list = []
        for row in rows:
            if pk not in row:
                raise IndexError(f"Primary key {pk!r} missing from struct.")
            payload = self._build_row_payload(schema, row, partial=False)
            params_list.append(tuple(payload[f] for f in ordered_fields))
        try:
            self._conn.executemany(
                f"INSERT INTO {self.table_name(map_name)} ({cols}) VALUES ({placeholders})",
                params_list,
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Duplicate key during bulk_insert into map {map_name!r}.") from exc
        self._dirty = True

    def count(self, map_name: str) -> int:
        self._require_schema(map_name)
        self.flush()
        cursor = self._conn.execute(f"SELECT COUNT(*) FROM {self.table_name(map_name)}")
        return cursor.fetchone()[0]

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
        try:
            self.flush()
        except Exception:
            pass
        try:
            self._conn.close()
        except Exception:
            pass


def _to_tuple_recursive(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_to_tuple_recursive(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_to_tuple_recursive(v) for v in value)
    return value
