"""Unit tests for the pure checkout rules: no database needed."""
from datetime import date

from loan_rules import (
    LOAN_PERIOD_DAYS, MAX_ACTIVE_LOANS, CheckoutFacts, check_checkout_rules, due_date_for,
)


def facts(**overrides) -> CheckoutFacts:
    base = dict(borrower_exists=True, active_loan_count=0, book_exists=True,
                book_available=True, has_unpaid_fines=False)
    base.update(overrides)
    return CheckoutFacts(**base)


def test_allowed_when_every_rule_is_satisfied():
    assert check_checkout_rules(facts()) is None


def test_limit_is_three_active_loans():
    assert MAX_ACTIVE_LOANS == 3
    assert check_checkout_rules(facts(active_loan_count=2)) is None
    assert check_checkout_rules(facts(active_loan_count=3)) == "Too many checkouts"


def test_each_rule_has_its_own_message():
    assert check_checkout_rules(facts(borrower_exists=False)) == "Borrower not found"
    assert check_checkout_rules(facts(book_exists=False)) == "Book doesn't exist"
    assert check_checkout_rules(facts(book_available=False)) == "Book already checked out."
    assert check_checkout_rules(facts(has_unpaid_fines=True)) == "Borrower has pending fines."


def test_order_of_checks_decides_which_message_wins():
    everything_wrong = facts(borrower_exists=False, active_loan_count=9, book_exists=False,
                             book_available=False, has_unpaid_fines=True)
    assert check_checkout_rules(everything_wrong) == "Borrower not found"


def test_due_date_is_14_days_after_checkout():
    assert LOAN_PERIOD_DAYS == 14
    assert due_date_for(date(2026, 1, 1)) == date(2026, 1, 15)
    assert due_date_for(date(2026, 2, 20)) == date(2026, 3, 6)   # crosses a month end
