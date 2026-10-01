"""Characterization tests: they pin down what the system does TODAY.

These must pass on the baseline commit, and they must still pass, unedited,
after the refactoring. Behaviour that is known to be wrong lives separately
in test_known_defects.py so it is never mixed into the refactoring gate.
"""
from datetime import date, timedelta

import pytest

import database as db
from conftest import START, set_today, some_isbns


# --------------------------------------------------------------- checkout
class TestCheckout:
    def test_successful_checkout_creates_loan_due_in_14_days(self, library):
        isbn = some_isbns(1)[0]

        result = db.create_loan(isbn, 1)

        assert result.status is True
        loans = db.get_loans_by_borrower_id(1)
        assert len(loans) == 1
        assert loans[0].isbn == isbn
        assert loans[0].date_out == START
        assert loans[0].due_date == START + timedelta(days=14)
        assert loans[0].date_in is None

    def test_unknown_borrower_is_rejected(self, library):
        result = db.create_loan(some_isbns(1)[0], 999_999)

        assert result.status is False
        assert result.message == "Borrower not found"

    def test_unknown_book_is_rejected(self, library):
        result = db.create_loan("NOT-AN-ISBN", 1)

        assert result.status is False
        assert result.message == "Book doesn't exist"

    def test_borrower_cannot_hold_more_than_three_books(self, library):
        a, b, c, d = some_isbns(4)
        for isbn in (a, b, c):
            assert db.create_loan(isbn, 1).status is True

        result = db.create_loan(d, 1)

        assert result.status is False
        assert result.message == "Too many checkouts"
        assert len(db.get_loans_by_borrower_id(1)) == 3

    def test_book_already_on_loan_cannot_be_checked_out_again(self, library):
        isbn = some_isbns(1)[0]
        assert db.create_loan(isbn, 1).status is True

        result = db.create_loan(isbn, 2)

        assert result.status is False
        assert result.message == "Book already checked out."

    def test_borrower_with_unpaid_fine_cannot_check_out(self, library):
        first, second = some_isbns(2)
        db.create_loan(first, 1)
        set_today(START + timedelta(days=20))   # 6 days overdue
        db.update_fines()
        db.checkin(db.get_loans_by_borrower_id(1)[0].id)

        result = db.create_loan(second, 1)

        assert result.status is False
        assert result.message == "Borrower has pending fines."

    def test_book_availability_follows_loan_state(self, library):
        isbn = some_isbns(1)[0]
        assert db.book_available_with_isbn(isbn) is True

        db.create_loan(isbn, 1)
        assert db.book_available_with_isbn(isbn) is False

        db.checkin(db.get_loans_by_borrower_id(1)[0].id)
        assert db.book_available_with_isbn(isbn) is True


# ---------------------------------------------------------------- checkin
class TestCheckin:
    def test_checkin_records_current_date(self, library):
        db.create_loan(some_isbns(1)[0], 1)
        set_today(START + timedelta(days=3))
        loan = db.get_loans_by_borrower_id(1)[0]

        result = db.checkin(loan.id)

        assert result.status is True
        assert db.get_loans_by_borrower_id(1) == []            # no active loans
        returned = db.get_loans_by_borrower_id(1, returned=True)[0]
        assert returned.date_in == START + timedelta(days=3)

    def test_checkin_many_returns_every_selected_book(self, library):
        for isbn in some_isbns(3):
            db.create_loan(isbn, 1)
        loans = db.get_loans_by_borrower_id(1)

        result = db.checkin_many(loans)

        assert result.status is True
        assert db.get_loans_by_borrower_id(1) == []


# ------------------------------------------------------------------ fines
class TestFines:
    def test_overdue_loan_is_fined_25_cents_per_day(self, library):
        db.create_loan(some_isbns(1)[0], 1)
        set_today(START + timedelta(days=14 + 10))            # 10 days late

        assert db.update_fines() is True

        fines = db.get_fines_by_borrower_id(1)
        assert [f.amt for f in fines] == [250]
        assert db.get_total_fines_by_borrower_id(1) == 250

    def test_loan_that_is_not_overdue_has_no_fine(self, library):
        db.create_loan(some_isbns(1)[0], 1)
        set_today(START + timedelta(days=14))                 # due today, not late

        db.update_fines()

        assert db.get_fines_by_borrower_id(1) == []

    def test_is_overdue_property(self, library):
        db.create_loan(some_isbns(1)[0], 1)
        loan = db.get_loans_by_borrower_id(1)[0]
        assert loan.is_overdue is False

        set_today(START + timedelta(days=15))
        assert loan.is_overdue is True

    def test_returned_loan_is_never_overdue(self, library):
        db.create_loan(some_isbns(1)[0], 1)
        db.checkin(db.get_loans_by_borrower_id(1)[0].id)
        set_today(START + timedelta(days=60))

        returned = db.get_loans_by_borrower_id(1, returned=True)[0]

        assert returned.is_overdue is False

    def _overdue_returned_borrower(self):
        """Borrower 1: 10 days late, book returned, fine 250 outstanding."""
        db.create_loan(some_isbns(1)[0], 1)
        set_today(START + timedelta(days=24))
        db.update_fines()
        db.checkin(db.get_loans_by_borrower_id(1)[0].id)

    def test_payment_below_total_is_rejected(self, library):
        self._overdue_returned_borrower()

        result = db.pay_fines(1, 100)

        assert result.status is False
        assert result.message == "Borrower didn't pay enough fine."

    def test_cannot_pay_fine_while_book_still_out(self, library):
        isbn = some_isbns(1)[0]
        db.create_loan(isbn, 1)
        set_today(START + timedelta(days=24))
        db.update_fines()                                      # fine exists, book not returned

        result = db.pay_fines(1, 250)

        assert result.status is False
        assert isbn in result.message
        assert "actively checked out" in result.message

    def test_paying_full_amount_after_return_clears_fines(self, library):
        self._overdue_returned_borrower()

        result = db.pay_fines(1, 250)

        assert result.status is True
        assert db.get_total_fines_by_borrower_id(1) == 0
        assert db.get_fines_by_borrower_id(1) == []

    def test_paying_when_no_fines_exist_is_rejected(self, library):
        result = db.pay_fines(1, 0)

        assert result.status is False
        assert result.message == "No fines attached to borrower."

    def test_paying_for_unknown_borrower_is_rejected(self, library):
        result = db.pay_fines(999_999, 100)

        assert result.status is False
        assert result.message == "Borrower doesn't exist."


# -------------------------------------------------------------- borrowers
class TestCreateBorrower:
    def test_valid_borrower_is_stored_with_normalised_ssn_and_phone(self, library):
        result = db.create_borrower("Ada Lovelace", "123-45-6789", "1 Main St", "(123) 456-7890")

        assert result.status is True
        stored = db.get_borrower_by_ssn("123456789")
        assert stored is not None
        assert stored.name == "Ada Lovelace"
        assert stored.phone == "1234567890"

    @pytest.mark.parametrize("name, ssn, address, phone, missing", [
        ("", "123-45-6789", "addr", "(123) 456-7890", "Name"),
        ("A", "", "addr", "(123) 456-7890", "SSN"),
        ("A", "123-45-6789", "", "(123) 456-7890", "Address"),
        ("A", "123-45-6789", "addr", "", "Phone"),
    ])
    def test_empty_fields_are_rejected_and_named(self, library, name, ssn, address, phone, missing):
        result = db.create_borrower(name, ssn, address, phone)

        assert result.status is False
        assert missing in result.message

    @pytest.mark.parametrize("ssn", ["12345678", "1234567890", "abc-de-fghi"])
    def test_invalid_ssn_is_rejected(self, library, ssn):
        result = db.create_borrower("A", ssn, "addr", "(123) 456-7890")

        assert result.status is False
        assert result.message == "Not a valid SSN."

    @pytest.mark.parametrize("phone", ["12345", "12345678901", "abcdefghij"])
    def test_invalid_phone_is_rejected(self, library, phone):
        result = db.create_borrower("A", "123-45-6789", "addr", phone)

        assert result.status is False
        assert result.message == "Not a valid Phone Number."

    def test_duplicate_ssn_is_rejected(self, library):
        db.create_borrower("A", "123-45-6789", "addr", "(123) 456-7890")

        result = db.create_borrower("B", "123456789", "other", "(999) 999-9999")

        assert result.status is False
        assert result.message == "Borrower with this SSN already exists."


# ----------------------------------------------------------------- search
class TestSearch:
    def test_search_books_by_title_is_case_insensitive(self, library):
        upper = db.search_books("CLASSICAL MYTHOLOGY")
        lower = db.search_books("classical mythology")

        assert upper and {b.isbn for b in upper} == {b.isbn for b in lower}

    def test_empty_search_returns_nothing(self, library):
        assert db.search_books("") == []
        assert db.search_borrowers("") == []

    def test_availability_filter_separates_loaned_books(self, library):
        isbn = "0195153448"
        db.create_loan(isbn, 1)

        available = {b.isbn for b in db.search_books(isbn, {"availability": "Available"})}
        unavailable = {b.isbn for b in db.search_books(isbn, {"availability": "Unavailable"})}

        assert isbn in unavailable
        assert isbn not in available

    def test_borrower_search_reports_loan_count_and_unpaid_fines(self, library):
        db.create_loan(some_isbns(1)[0], 1)
        set_today(START + timedelta(days=24))
        db.update_fines()

        row = next(r for r in db.search_borrowers("1") if r.id == 1)

        assert row.active_loan_count == 1
        assert row.total_unpaid_fines == 250
