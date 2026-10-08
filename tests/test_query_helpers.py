"""Characterization tests for the low-level SQL helpers in database/query/query.py."""
import os
import sqlite3

from database import config
from database.query import query


def test_get_one_or_none_returns_a_row_with_named_columns(library):
    row = query.get_one_or_none("SELECT Bname FROM BORROWER WHERE Card_id = ?", [1])

    assert row is not None
    assert row["Bname"]


def test_get_one_or_none_returns_none_when_nothing_matches(library):
    assert query.get_one_or_none("SELECT * FROM BORROWER WHERE Card_id = ?", [-1]) is None


def test_get_all_or_none_returns_every_row(library):
    rows = query.get_all_or_none("SELECT Card_id FROM BORROWER WHERE Card_id <= ? ORDER BY Card_id", [3])

    assert [r["Card_id"] for r in rows] == [1, 2, 3]


def test_reads_return_none_when_the_database_file_is_missing(library, tmp_path):
    config.db_name = str(tmp_path / "does_not_exist.db")

    assert query.get_one_or_none("SELECT 1", []) is None
    assert query.get_all_or_none("SELECT 1", []) is None
    assert not os.path.exists(config.db_name)       # reading must not create the file


def test_reads_return_none_on_invalid_sql_instead_of_raising(library):
    assert query.get_one_or_none("SELECT nonsense FROM nowhere", []) is None
    assert query.get_all_or_none("SELECT nonsense FROM nowhere", []) is None


def test_try_execute_one_commits_and_reports_success(library):
    ok = query.try_execute_one("INSERT INTO metadata (key, value) VALUES (?, ?)", ["k", "v"])

    assert ok is True
    assert query.get_one_or_none("SELECT value FROM metadata WHERE key = ?", ["k"])["value"] == "v"


def test_try_execute_one_reports_failure_on_constraint_violation(library):
    query.try_execute_one("INSERT INTO metadata (key, value) VALUES (?, ?)", ["dup", "1"])

    ok = query.try_execute_one("INSERT INTO metadata (key, value) VALUES (?, ?)", ["dup", "2"])

    assert ok is False
    assert query.get_one_or_none("SELECT value FROM metadata WHERE key = ?", ["dup"])["value"] == "1"


def test_try_execute_many_is_all_or_nothing(library):
    rows = [("a", "1"), ("b", "2"), ("a", "3")]       # duplicate key on the third row

    ok = query.try_execute_many("INSERT INTO metadata (key, value) VALUES (?, ?)", rows)

    assert ok is False
    assert query.get_one_or_none("SELECT 1 FROM metadata WHERE key IN ('a','b')", []) is None


def test_try_execute_many_commits_every_row_on_success(library):
    ok = query.try_execute_many("INSERT INTO metadata (key, value) VALUES (?, ?)", [("x", "1"), ("y", "2")])

    assert ok is True
    assert len(query.get_all_or_none("SELECT * FROM metadata WHERE key IN ('x','y')", [])) == 2
