"""Shared fixtures for the characterization tests.

Every test gets its own throw-away SQLite database, built once from the real
CSV data and copied per test, so tests never touch the developer's library.db
and never depend on each other.
"""
import os
import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import database as db  # noqa: E402  (must come after sys.path change)
from database import config  # noqa: E402

START = date(2026, 1, 1)  # fixed "today" so date maths is deterministic


@pytest.fixture(scope="session")
def template_db(tmp_path_factory):
    """Build the database once (the CSV import is the slow part)."""
    cwd = os.getcwd()
    os.chdir(REPO_ROOT)  # import_data opens 'data/book.csv' relative to cwd
    try:
        path = str(tmp_path_factory.mktemp("template") / "template.db")
        assert db.init(path), "database initialisation failed"
    finally:
        os.chdir(cwd)
    return path


@pytest.fixture
def library(template_db, tmp_path):
    """A fresh, initialised database with the clock fixed at START."""
    path = str(tmp_path / "test.db")
    shutil.copy(template_db, path)
    config.db_name = path
    db.set_current_date(START)
    db.set_fines_updated(START)
    return path


def set_today(value: date) -> None:
    db.set_current_date(value)


def some_isbns(n: int) -> list[str]:
    """Return n ISBNs that exist in the database."""
    conn = sqlite3.connect(config.db_name)
    rows = conn.execute("SELECT Isbn FROM BOOK ORDER BY Isbn LIMIT ?", (n,)).fetchall()
    conn.close()
    return [r[0] for r in rows]
