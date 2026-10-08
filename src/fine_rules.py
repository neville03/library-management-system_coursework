"""Business rule for late fines. Pure logic: no database, no clock."""
from datetime import date

FINE_CENTS_PER_DAY = 25


def days_overdue(due_date: date, today: date) -> int:
    return (today - due_date).days


def calculate_fine_cents(due_date: date, today: date) -> int:
    """Fine in cents for a loan that is still out on `today`."""
    return days_overdue(due_date, today) * FINE_CENTS_PER_DAY
