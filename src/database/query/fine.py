from typing import Optional
from datetime import date

from models import FineSearchResult #imported
# from fine_rules import calculate_fine_cents
from fine_rules import FinePolicy, PerDayFinePolicy
from database.names import (
    FINES_TABLE_NAME,
    BOOK_LOANS_TABLE_NAME,
    BOOKS_TABLE_NAME
)

import database as db
from models.result import OperationResult

from . import query, metadata

def get_all_fines(paid: bool = False) -> list[FineSearchResult]:
    sql = f"""
    SELECT
        f.Loan_id,
        b.Isbn,
        l.Card_id,
        f.Fine_amt,
        f.Paid,
        l.Date_out,
        l.Due_date,
        l.Date_in
    FROM {FINES_TABLE_NAME} f
    JOIN {BOOK_LOANS_TABLE_NAME} l ON l.Loan_id = f.Loan_id
    JOIN {BOOKS_TABLE_NAME} b ON b.Isbn = l.Isbn
    {'WHERE f.Paid = 0' if not paid else ''}
    ORDER BY l.Date_out DESC
    """

    results = query.get_all_or_none(sql, [])

    if not results:
        return []

    return [FineSearchResult(**dict(result)) for result in results]

def get_fines_by_borrower_id(borrower_id: int, paid: bool = False) -> list[FineSearchResult]:
    sql = f"""
    SELECT
        f.Loan_id,
        b.Isbn,
        l.Card_id,
        f.Fine_amt,
        f.Paid,
        l.Date_out,
        l.Due_date,
        l.Date_in
    FROM {FINES_TABLE_NAME} f
    JOIN {BOOK_LOANS_TABLE_NAME} l ON l.Loan_id = f.Loan_id
    JOIN {BOOKS_TABLE_NAME} b ON b.Isbn = l.Isbn
    WHERE l.Card_id = ? {'AND f.Paid = 0' if not paid else ''}
    ORDER BY l.Date_out DESC
    """

    params = [borrower_id] if borrower_id else []

    results =  query.get_all_or_none(sql, params)

    if not results:
        return []

    return [FineSearchResult(**dict(result)) for result in results]

def get_total_fines_by_borrower_id(borrower_id: int, paid: bool = False) -> int:
    fines = db.get_fines_by_borrower_id(borrower_id, paid=paid)

    if not fines:
        return 0

    total_fines = sum(fine.amt for fine in fines)

    return total_fines

def set_fines_updated(value: date) -> bool:
    return metadata.set_value('last_updated_fines', value.isoformat())

def get_fines_last_updated() -> Optional[date]:
    result = metadata.get_value('last_updated_fines')

    if not result:
        return None

    return date.fromisoformat(result)

def pay_fines(borrower_id: int, amt: int) -> OperationResult:
    borrower = db.get_borrower_by_id(borrower_id)

    if not borrower:
        return OperationResult(
            status=False,
            message="Borrower doesn't exist."
        )

    total_fines = db.get_total_fines_by_borrower_id(borrower.id)

    if amt < total_fines:
        return OperationResult(
            status=False,
            message="Borrower didn't pay enough fine."
        )

    fines = db.get_fines_by_borrower_id(borrower.id)

    if not fines:
        return OperationResult(
            status=False,
            message="No fines attached to borrower."
        )

    isbn_of_fines_with_active_checkouts = [fine.isbn for fine in fines if fine.date_in == None]
    isbns = ", ".join(isbn_of_fines_with_active_checkouts)

    if isbn_of_fines_with_active_checkouts:
        return OperationResult(
            status=False,
            message=f"Cannot make payment on books that are actively checked out: {isbns}"
        )

    loan_ids = [fine.loan_id for fine in fines]

    return OperationResult(
            status=db.resolve_fines(loan_ids),
            message="Fines paid successfully!"
        )

def resolve_fines(loan_ids: list[int]) -> bool:
    sql = f"""
        UPDATE {FINES_TABLE_NAME}
        SET Paid = 1
        WHERE Loan_id = ?
    """

    params = [(loan_id,) for loan_id in loan_ids]

    return query.try_execute_many(sql, params)

def update_fines(
    policy: FinePolicy = PerDayFinePolicy()
) -> bool:
    last_update = db.get_fines_last_updated()
    today = db.get_current_date()

    if not today:
        return False

    should_update = (last_update is None) or (last_update <= today)

    if not should_update:
        return True

    overdue_loans = db.get_all_loans(overdue=True)

    if not overdue_loans:
        db.set_fines_updated(today)
        return True

    fines_to_update = []

    for loan in overdue_loans:
        fine_amt = policy.calculate_fine_cents(
            loan.due_date,
            today
        )

        fines_to_update.append((loan.id, fine_amt))

    success = db.set_fines(fines_to_update)

    if success:
        db.set_fines_updated(today)
        return True

    return False

def set_fines(fines: list[tuple]) -> bool:
    sql = f"""
        INSERT OR REPLACE INTO {FINES_TABLE_NAME} (
            Loan_id,
            Fine_amt,
            Paid
        ) VALUES (
            ?,
            ?,
            0
        )
    """

    if not fines:
        return True

    params = fines

    return query.try_execute_many(sql, params)
