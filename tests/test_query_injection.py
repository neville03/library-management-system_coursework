"""The query helpers depend on the Database abstraction, so one can be injected."""
import pytest

from database.connection import SqliteDatabase
from database.query import query


@pytest.fixture
def restore_database():
    original = query._database
    yield
    query.set_database(original)


def test_helpers_use_the_injected_database(library, tmp_path, restore_database):
    other = SqliteDatabase(lambda: str(tmp_path / "other.db"))
    query.set_database(other)

    assert query.try_execute_one("CREATE TABLE t (x INTEGER)", []) is True
    assert query.try_execute_one("INSERT INTO t (x) VALUES (?)", [7]) is True
    assert query.get_one_or_none("SELECT x FROM t", [])["x"] == 7

    # the library database from config was never touched
    query.set_database(SqliteDatabase())
    assert query.get_one_or_none("SELECT * FROM t", []) is None


def test_helpers_work_with_a_fake_database(restore_database):
    class FakeDatabase:
        errors = (RuntimeError,)

        def exists(self):
            return False

        def connect(self, named_columns=False):
            raise AssertionError("must not connect when the database is missing")

    query.set_database(FakeDatabase())

    assert query.get_one_or_none("SELECT 1", []) is None
    assert query.get_all_or_none("SELECT 1", []) is None
