"""Business rule for late fines. Pure logic: no database, no clock."""
from datetime import date
from dataclasses import dataclass
from typing import Protocol

FINE_CENTS_PER_DAY = 25


def days_overdue(due_date: date, today: date) -> int:
    return (today - due_date).days


# def calculate_fine_cents(due_date: date, today: date) -> int:
#     """Fine in cents for a loan that is still out on `today`."""
#     return days_overdue(due_date, today) * FINE_CENTS_PER_DAY


# --- Open/Closed: new pricing rules are new classes, not edits to old code ---

class FinePolicy(Protocol):
    def calculate_fine_cents(self, due_date: date, today: date) -> int: ...
 
 
@dataclass(frozen=True)
class PerDayFinePolicy:
    cents_per_day: int = FINE_CENTS_PER_DAY
 
    def calculate_fine_cents(self, due_date: date, today: date) -> int:
        return max(0, days_overdue(due_date, today)) * self.cents_per_day
 
 
@dataclass(frozen=True)
class CappedFinePolicy:
    """Example extension: wraps any policy and caps the result."""
    inner: FinePolicy
    cap_cents: int
 
    def calculate_fine_cents(self, due_date: date, today: date) -> int:
        return min(self.inner.calculate_fine_cents(due_date, today), self.cap_cents)
 
