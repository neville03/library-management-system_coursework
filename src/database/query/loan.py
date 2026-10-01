from datetime import date, timedelta

from database.names import (
    BOOK_LOANS_TABLE_NAME,
)

from models import Loan

import database as db
from models.result import OperationResult

from . import query

def search_loans(isbn: str | None = None,
                 borrower_id: str | None = None,
                 name: str | None = None,
                 returned: bool = False) -> list[Loan]:
    sql = f"""
SELECT
l.Loan_id,
l.Isbn,
l.Card_id,
b.Title,
l.Date_out,
l.Due_date,
l.Date_in
FROM BOOK_LOANS l
JOIN BOOK b ON b.Isbn = l.Isbn
JOIN BORROWER br ON br.Card_id = l.Card_id
        """

    conditions = []
    params = []

    if not returned:
        sql += ' WHERE l.Date_in IS NULL'

    if isbn:
        conditions.append("l.Isbn LIKE ? COLLATE NOCASE")
        params.append(f"%{isbn}%")

    if borrower_id:
        conditions.append("br.Card_id LIKE ?")
        params.append(f"%{borrower_id}%")

    if name:
        conditions.append("br.Bname LIKE ? COLLATE NOCASE")
        params.append(f"%{name}%")

    if conditions:
        if returned:
            sql += " WHERE (" + " OR ".join(conditions) + ")"
        else:
            sql += " AND (" + " OR ".join(conditions) + ")"

    sql += " ORDER BY l.Date_out DESC"

    results = query.get_all_or_none(sql, params)

    if not results:
        return []

    return [Loan(**dict(result)) for result in results]

def get_all_loans(overdue: bool = False, returned: bool = False) -> list[Loan]:
    loans = db.search_loans(returned=returned)

    if not overdue:
        return loans

    today = db.get_current_date()

    return [loan for loan in loans if loan.is_overdue_on(today)]

def get_loans_by_borrower_id(borrower_id: int, returned: bool = False) -> list[Loan]:
    sql = f"""
SELECT
l.Loan_id,
l.Isbn,
l.Card_id,
b.Title,
l.Date_out,
l.Due_date,
l.Date_in
FROM BOOK_LOANS l
JOIN BOOK b ON b.Isbn = l.Isbn
WHERE l.Card_id = ?
        """

    if not returned:
        sql += " AND l.Date_in IS NULL"

    sql += " ORDER BY l.Date_out DESC"

    results = query.get_all_or_none(sql, [borrower_id])

    if not results:
        return []

    return [Loan(**dict(result)) for result in results]

def get_loans_by_isbn(isbn: str, returned: bool = False) -> list[Loan]:
    sql = f"""
SELECT
l.Loan_id,
l.Isbn,
l.Card_id,
b.Title,
l.Date_out,
l.Due_date,
l.Date_in
FROM BOOK_LOANS l
JOIN BOOK b ON b.Isbn = l.Isbn
WHERE l.Isbn = ?
        """

    if not returned:
        sql += " AND l.Date_in IS NULL"

    sql += " ORDER BY l.Date_out DESC"

    results = query.get_all_or_none(sql, [isbn])

    if not results:
        return []

    return [Loan(**dict(result)) for result in results]

def checkout(isbn: str, borrower_id: int) -> OperationResult:
    return db.create_loan(isbn, borrower_id)

def create_loan(isbn: str, borrower_id: int) -> OperationResult:
    borrower = db.get_borrower_by_id(borrower_id)

    if not borrower:
        return OperationResult(
            status=False,
            message="Borrower not found"
        )

    checkouts = db.get_loans_by_borrower_id(borrower_id, returned=False)

    if checkouts and len(checkouts) >= 3:
        return OperationResult(
            status=False,
            message="Too many checkouts"
        )

    book = db.get_book_by_isbn(isbn)

    if not book:
        return OperationResult(
            status=False,
            message="Book doesn't exist"
        )

    book_available = db.book_available_with_isbn(isbn)

    if not book_available:
        return OperationResult(
            status=False,
            message="Book already checked out."
        )

    borrowers_fines = db.get_fines_by_borrower_id(borrower_id)

    if borrowers_fines and len(borrowers_fines) > 0:
        return OperationResult(
            status=False,
            message="Borrower has pending fines."
        )

    sql = f"""
        INSERT INTO {BOOK_LOANS_TABLE_NAME} (
Isbn,
Card_id,
Date_out,
Due_date,
Date_in
) VALUES (?, ?, ?, ?, NULL)
        """

    today = db.get_current_date() or date.today()

    date_out = today.isoformat()
    due_date = (today + timedelta(days=14)).isoformat()

    params = [isbn, borrower_id, date_out, due_date]

    return OperationResult(
        status=query.try_execute_one(sql, params),
        message="Book successfully checked out!"
    )

def checkin_many(loans: list[Loan]) -> OperationResult:
    isbns=[]

    for loan in loans:
        success = db.checkin(loan.id).status

        if not success:
            isbns.append(loan.isbn)

    return OperationResult(
        status=not isbns,
        message="Books checked in successfully." if not isbns else f"Failed to check in: {', '.join(isbns)}.]"
    )

def checkin(loan_id: int) -> OperationResult:
    return db.resolve_loan(loan_id)

def resolve_loan(loan_id: int) -> OperationResult:
    sql = f"""
        UPDATE {BOOK_LOANS_TABLE_NAME}
SET Date_in = ?
WHERE Loan_id = ?
        """

    today = db.get_current_date() or date.today()
    date_in = today.isoformat()

    params = [date_in, loan_id]

    success = query.try_execute_one(sql, params)

    return OperationResult(
        status=success,
        message="Book check in successfully."
    )