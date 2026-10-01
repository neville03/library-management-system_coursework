import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

from database import config


@contextmanager
def _connection(named_columns: bool = False) -> Iterator[sqlite3.Connection]:
    """Open the configured database and always close it again."""
    conn = sqlite3.connect(config.db_name)

    if named_columns:
        conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()


def _read(sql: str, params: list, fetch: Callable[[sqlite3.Cursor], Any]) -> Optional[Any]:
    if not os.path.isfile(config.db_name):
        return None

    with _connection(named_columns=True) as conn:
        try:
            return fetch(conn.execute(sql, params))
        except sqlite3.Error as e:
            print(e)
            return None


def _write(sql: str, params: list, many: bool) -> bool:
    with _connection() as conn:
        try:
            cursor = conn.cursor()
            (cursor.executemany if many else cursor.execute)(sql, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return False


def get_one_or_none(sql: str, params: list) -> Optional[Any]:
    return _read(sql, params, lambda cursor: cursor.fetchone())


def get_all_or_none(sql: str, params: list) -> Optional[list]:
    return _read(sql, params, lambda cursor: cursor.fetchall())


def try_execute_many(sql: str, params: list) -> bool:
    return _write(sql, params, many=True)


def try_execute_one(sql: str, params: list) -> bool:
    return _write(sql, params, many=False)
