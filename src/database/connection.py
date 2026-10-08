import os
import sqlite3
from typing import Callable, Protocol

from database import config


class Database(Protocol):
    """What the query helpers need from a database, without naming a driver."""

    errors: tuple[type[Exception], ...]

    def exists(self) -> bool: ...

    def connect(self, named_columns: bool = False) -> sqlite3.Connection: ...


class SqliteDatabase:
    """The concrete SQLite database the application runs on."""

    errors = (sqlite3.Error,)

    def __init__(self, path: Callable[[], str] = lambda: config.db_name):
        # A callable, not a string, so the path is read on every call and
        # still follows config.set_db_name() after the app starts.
        self._path = path

    def exists(self) -> bool:
        return os.path.isfile(self._path())

    def connect(self, named_columns: bool = False) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path())

        if named_columns:
            conn.row_factory = sqlite3.Row

        return conn
