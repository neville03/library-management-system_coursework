"""Tests that EXPOSE the Q1 design problem (models depend on the database).

They are written BEFORE the refactor. On the baseline they FAIL, which is the
evidence that the fault exists. After the refactor they PASS.
"""
import shutil
import sqlite3
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import database as db
from database import config
from conftest import START, set_today, some_isbns

SRC = Path(__file__).resolve().parent.parent / "src"


def test_models_can_be_imported_on_their_own():
    """A domain model must not need the database layer just to be imported."""
    result = subprocess.run(
        [sys.executable, "-c", "import models"],
        cwd=SRC, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr.strip().splitlines()[-1]


def _connections_to_find_overdue_loans(template_db, tmp_path, loan_count, monkeypatch) -> int:
    """Fresh database, `loan_count` overdue loans, then count connections opened."""
    path = str(tmp_path / f"loans_{loan_count}.db")
    shutil.copy(template_db, path)
    config.db_name = path
    db.set_current_date(START)

    for card_id, isbn in enumerate(some_isbns(loan_count), start=1):
        assert db.create_loan(isbn, card_id).status is True
    set_today(START + timedelta(days=60))                    # every loan is now overdue

    opened = {"n": 0}
    real_connect = sqlite3.connect

    def counting_connect(*args, **kwargs):
        opened["n"] += 1
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", counting_connect)
    found = db.get_all_loans(overdue=True)
    monkeypatch.setattr(sqlite3, "connect", real_connect)

    assert len(found) == loan_count
    return opened["n"]


def test_overdue_check_cost_does_not_grow_with_the_number_of_loans(template_db, tmp_path, monkeypatch):
    """Today it opens one extra database connection for every loan checked."""
    few = _connections_to_find_overdue_loans(template_db, tmp_path, 2, monkeypatch)
    many = _connections_to_find_overdue_loans(template_db, tmp_path, 6, monkeypatch)

    assert many == few, f"2 loans used {few} connections but 6 loans used {many}"
