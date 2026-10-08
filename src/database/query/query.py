from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

from database.connection import Database, SqliteDatabase

_database: Database = SqliteDatabase()


def set_database(database: Database) -> None:
    """Swap the database the helpers talk to (e.g. a test or another backend)."""
    global _database
    _database = database


@contextmanager
def _connection(named_columns: bool = False) -> Iterator[Any]:
    """Open the injected database and always close it again."""
    conn = _database.connect(named_columns)

    try:
        yield conn
    finally:
        conn.close()


def _read(sql: str, params: list, fetch: Callable[[Any], Any]) -> Optional[Any]:
    if not _database.exists():
        return None

    with _connection(named_columns=True) as conn:
        try:
            return fetch(conn.execute(sql, params))
        except _database.errors as e:
            print(e)
            return None


def _write(sql: str, params: list, many: bool) -> bool:
    with _connection() as conn:
        try:
            cursor = conn.cursor()
            (cursor.executemany if many else cursor.execute)(sql, params)
            conn.commit()
            return True
        except _database.errors as e:
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
