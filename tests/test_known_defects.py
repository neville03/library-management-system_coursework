"""Tests that pin down KNOWN DEFECTS in the baseline.

Each test asserts the CURRENT (wrong) behaviour, so it passes on the baseline
and documents the problem with evidence. When a defect is fixed (Q3/Q4), the
matching test must be inverted to assert the correct behaviour, and the change
recorded in the report. Keep these out of the Q2 refactoring gate: refactoring
must not change behaviour, defect fixes deliberately do.
"""
import os
import sqlite3
from datetime import timedelta

import pytest

import database as db
from database import config
from database.query import query as query_module
from conftest import START, set_today, some_isbns


def test_DEFECT_partial_isbn_resolves_to_a_different_book(library):
    """'Exact' ISBN lookup is really a LIKE '%...%' search (book.py:79-85)."""
    book = db.get_book_by_isbn("0195153")          # only a prefix of a real ISBN

    assert book is not None
    assert book.isbn == "0195153448"


def test_DEFECT_failed_borrower_insert_still_reports_success_message(library, monkeypatch):
    monkeypatch.setattr(query_module, "try_execute_one", lambda sql, params: False)

    result = db.create_borrower("A", "123-45-6789", "addr", "(123) 456-7890")

    assert result.status is False
    assert result.message == "Borrower created successfuly!"      # misleading


def test_DEFECT_failed_checkout_insert_still_reports_success_message(library, monkeypatch):
    monkeypatch.setattr(query_module, "try_execute_one", lambda sql, params: False)

    result = db.create_loan(some_isbns(1)[0], 1)

    assert result.status is False
    assert result.message == "Book successfully checked out!"     # misleading


def test_DEFECT_checkin_of_nonexistent_loan_reports_success(library):
    result = db.checkin(424_242)

    assert result.status is True
    assert result.message == "Book check in successfully."


def test_DEFECT_late_return_does_not_update_the_fine(library):
    """Fines are only recalculated by update_fines() for UNRETURNED loans."""
    db.create_loan(some_isbns(1)[0], 1)
    set_today(START + timedelta(days=31))          # due day 14 -> 17 days late
    db.update_fines()
    assert [f.amt for f in db.get_fines_by_borrower_id(1)] == [425]

    set_today(START + timedelta(days=40))          # returned 26 days late
    db.checkin(db.get_loans_by_borrower_id(1)[0].id)
    db.update_fines()

    assert [f.amt for f in db.get_fines_by_borrower_id(1)] == [425]   # should be 650


def test_DEFECT_foreign_keys_are_not_enforced(library):
    conn = sqlite3.connect(config.db_name)
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 0
    conn.execute(
        "INSERT INTO BOOK_LOANS (Isbn, Card_id, Date_out, Due_date) "
        "VALUES ('NO-SUCH-BOOK', -5, '2026-01-01', '2026-01-15')"
    )
    conn.commit()                                   # no IntegrityError raised
    conn.close()


def test_DEFECT_unwritable_database_path_raises_instead_of_failing_gracefully(library, tmp_path):
    config.db_name = str(tmp_path / "missing_dir" / "x.db")

    with pytest.raises(sqlite3.OperationalError):
        db.create_borrower("A", "123-45-6789", "addr", "(123) 456-7890")


def test_DEFECT_ssn_is_stored_in_plaintext(library):
    conn = sqlite3.connect(config.db_name)
    (ssn,) = conn.execute("SELECT Ssn FROM BORROWER WHERE Card_id = 1").fetchone()
    conn.close()

    assert ssn.replace("-", "").isdigit() and len(ssn.replace("-", "")) == 9
