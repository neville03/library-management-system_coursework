from typing import Optional

from models import BorrowerSearchResult, Borrower

from database.names import (
    BOOK_LOANS_TABLE_NAME,
    BORROWERS_TABLE_NAME,
    FINES_TABLE_NAME
)

import database as db
from models.result import OperationResult

from . import query


def search_borrowers(search_term: str) -> list[BorrowerSearchResult]:
    if not search_term:
        return []

    sql = f"""
        SELECT
            b.Card_id,
            b.Bname,
            COUNT(
                DISTINCT CASE
                    WHEN l.Date_in IS NULL
                    THEN l.Loan_id
                END
            ) as N_Active_loans,
            COALESCE(SUM(
                CASE
                    WHEN f.Paid = 0
                    THEN f.Fine_amt
                    ELSE 0
                END
            ), 0) as Outstanding_fines
        FROM {BORROWERS_TABLE_NAME} b
        LEFT JOIN {BOOK_LOANS_TABLE_NAME} l ON b.Card_id = l.Card_id
        LEFT JOIN {FINES_TABLE_NAME} f ON l.Loan_id = f.Loan_id
        WHERE LOWER(b.Bname) LIKE LOWER(?)
           OR CAST(b.Card_id AS TEXT) LIKE ?
        GROUP BY b.Card_id, b.Bname
        ORDER BY b.Card_id;
    """

    params = [f"%{search_term}%" for _ in range(2)]

    results = query.get_all_or_none(sql, params)

    if not results:
        return []

    return [BorrowerSearchResult(**dict(result)) for result in results]

_SELECT_BORROWER_BY_SSN = """
    SELECT b.Card_id, b.Ssn, b.Bname, b.Address, b.Phone
    FROM BORROWER b
    WHERE b.Ssn = ?
"""

_SELECT_BORROWER_BY_ID = """
    SELECT b.Card_id, b.Ssn, b.Bname, b.Address, b.Phone
    FROM BORROWER b
    WHERE b.Card_id = ?
"""

def get_borrower_by_ssn(ssn: str) -> Optional[Borrower]:
    return _get_borrower(_SELECT_BORROWER_BY_SSN, ssn)

def get_borrower_by_id(borrower_id: int) -> Optional[Borrower]:
    return _get_borrower(_SELECT_BORROWER_BY_ID, str(borrower_id))

def _get_borrower(sql: str, param: str) -> Optional[Borrower]:
    result = query.get_one_or_none(sql, [param])

    if not result:
        return None

    return Borrower(**dict(result))


def create_borrower(name: str, ssn: str, address: str, phone: str) -> OperationResult:
    if not (name and ssn and address and phone):
        missing_fields = []
        if not name:
            missing_fields.append("Name")
        if not ssn:
            missing_fields.append("SSN")
        if not address:
            missing_fields.append("Address")
        if not phone:
            missing_fields.append("Phone")

        return OperationResult(
            status=False,
            message=f"Missing field(s): {', '.join(missing_fields)}"
        )

    ssn = ssn.replace('-', '')

    if not ssn.isnumeric() or len(ssn) != 9:
        return OperationResult(
            status=False,
            message="Not a valid SSN."
        )

    phone = phone.replace('(', '').replace(')', '').replace('-','').replace(' ', '')

    if not phone.isnumeric() or len(phone) != 10:
        return OperationResult(
            status=False,
            message="Not a valid Phone Number."
        )

    borrower = db.get_borrower_by_ssn(ssn)

    if borrower:
        return OperationResult(
            status=False,
            message="Borrower with this SSN already exists."
        )

    sql = f"""
    INSERT INTO {BORROWERS_TABLE_NAME} (
        Bname,
        Ssn,
        Address,
        Phone
    ) VALUES (?, ?, ?, ?)
    """

    params = [name, ssn, address, phone]

    succeeded = query.try_execute_one(sql, params)

    return OperationResult(
        status=succeeded,
        message="Borrower created successfully!" if succeeded else "Could not save the borrower."
    )
