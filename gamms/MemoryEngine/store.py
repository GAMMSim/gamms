from gamms.typing.memory_engine import IStore
from typing import Any, Dict, List
import sqlite3

class TableStore(IStore):
    def __init__(
        self,
        conn: sqlite3.Connection,
        name: str,
        schema: Dict[str, str],
        primary_key: str
    ):
        """
        Generic SQL table-backed store.
        schema: column_name -> SQL type
        primary_key: name of the primary key column
        """
        self.conn = conn
        self.name = name
        cols = ", ".join(f"{c} {t}" for c, t in schema.items())
        sql = f"""
            CREATE TABLE IF NOT EXISTS {name} (
              {cols},
              PRIMARY KEY ({primary_key})
            )
        """
        conn.execute(sql)
        conn.commit()

    def save(self, obj: Dict[str, Any]) -> None:
        """
        Insert or update a row. obj maps column -> value.
        """
        cols = ", ".join(obj.keys())
        placeholders = ", ".join("?" for _ in obj)
        sql = f"REPLACE INTO {self.name}({cols}) VALUES({placeholders})"
        self.conn.execute(sql, tuple(obj.values()))
        self.conn.commit()

    def load(self, key: Any) -> Dict[str, Any]:
        """
        Load a row by primary key (assumes primary key column named 'id').
        """
        sql = f"SELECT * FROM {self.name} WHERE id = ?"
        cur = self.conn.execute(sql, (key,))
        row = cur.fetchone()
        if not row:
            raise KeyError(f"{self.name} no row for id={key}")
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    def delete(self, key: Any) -> None:
        sql = f"DELETE FROM {self.name} WHERE id = ?"
        self.conn.execute(sql, (key,))
        self.conn.commit()