# """Unit tests for the pure fine rule: no database needed."""
# from datetime import date

# from fine_rules import FINE_CENTS_PER_DAY, calculate_fine_cents, days_overdue

# DUE = date(2026, 1, 15)


# def test_rate_is_25_cents_per_day():
#     assert FINE_CENTS_PER_DAY == 25


# def test_days_overdue_counts_calendar_days():
#     assert days_overdue(DUE, date(2026, 1, 25)) == 10
#     assert days_overdue(DUE, date(2026, 2, 1)) == 17


# def test_fine_scales_linearly_with_days_late():
#     assert calculate_fine_cents(DUE, date(2026, 1, 16)) == 25
#     assert calculate_fine_cents(DUE, date(2026, 1, 25)) == 250
#     assert calculate_fine_cents(DUE, date(2026, 2, 1)) == 425


# def test_no_fine_on_the_due_date_itself():
#     assert calculate_fine_cents(DUE, DUE) == 0

from datetime import date

from fine_rules import FINE_CENTS_PER_DAY, PerDayFinePolicy, days_overdue

DUE = date(2026, 1, 15)

policy = PerDayFinePolicy()


def test_rate_is_25_cents_per_day():
    assert FINE_CENTS_PER_DAY == 25


def test_days_overdue_counts_calendar_days():
    assert days_overdue(DUE, date(2026, 1, 25)) == 10
    assert days_overdue(DUE, date(2026, 2, 1)) == 17


def test_fine_scales_linearly_with_days_late():
    assert policy.calculate_fine_cents(DUE, date(2026, 1, 16)) == 25
    assert policy.calculate_fine_cents(DUE, date(2026, 1, 25)) == 250
    assert policy.calculate_fine_cents(DUE, date(2026, 2, 1)) == 425


def test_no_fine_on_the_due_date_itself():
    assert policy.calculate_fine_cents(DUE, DUE) == 0
