"""Business rules for lending a book.

Pure logic: no database, no clock, no UI. Everything the rules need is passed
in, so they can be tested in milliseconds and changed without touching SQL.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

MAX_ACTIVE_LOANS = 3
LOAN_PERIOD_DAYS = 14


@dataclass(frozen=True)
class CheckoutFacts:
    borrower_exists: bool
    active_loan_count: int
    book_exists: bool
    book_available: bool
    has_unpaid_fines: bool


def check_checkout_rules(facts: CheckoutFacts) -> Optional[str]:
    """Return the reason a checkout is refused, or None if it is allowed.

    The order of the checks is part of the behaviour (it decides which message
    the librarian sees first), so it must not change.
    """
    if not facts.borrower_exists:
        return "Borrower not found"

    if facts.active_loan_count >= MAX_ACTIVE_LOANS:
        return "Too many checkouts"

    if not facts.book_exists:
        return "Book doesn't exist"

    if not facts.book_available:
        return "Book already checked out."

    if facts.has_unpaid_fines:
        return "Borrower has pending fines."

    return None


def due_date_for(checked_out_on: date) -> date:
    return checked_out_on + timedelta(days=LOAN_PERIOD_DAYS)
