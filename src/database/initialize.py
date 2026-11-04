import sqlite3
from pathlib import Path
import os

from database.dtypes import CSVData
from database.names import (
    BOOKS_TABLE_NAME,
    BOOK_AUTHORS_TABLE_NAME,
    AUTHORS_TABLE_NAME,
    BORROWERS_TABLE_NAME,
)
from database import schema, config

from database.import_data import from_csv

import database as db

def init(db_name: str) -> bool:
    config.set_db_name(db_name)

    data = from_csv()

    if not data:
        return False

    created = _create_database()

    if not created:
        return False

    print(db_name)

    db.set_initialized()

    return _insert_data(data)

def exists(db_name: str) -> bool:
    return Path(db_name).is_file()

def delete(db_name: str) -> bool:
    if os.path.exists(db_name):
        os.remove(db_name)

        return True

    return False

def _create_database() -> bool:
    conn = sqlite3.connect(config.db_name)
    c = conn.cursor()

    c.execute(schema.queries['books'])
    c.execute(schema.queries['book_authors'])
    c.execute(schema.queries['authors'])
    c.execute(schema.queries['borrowers'])
    c.execute(schema.queries['loans'])
    c.execute(schema.queries['fines'])
    c.execute(schema.queries['metadata'])

    conn.close()

    return True

def _insert_data(data: CSVData) -> bool:
    (books, book_authors, authors, borrowers) = data

    conn = sqlite3.connect(config.db_name)
    c = conn.cursor()

    def try_insert(sql_query: str, data_values) -> bool:
        # TODO: logging

        try:
            c.executemany(sql_query, data_values)
            conn.commit()
        except sqlite3.Error:
            conn.rollback()

            return False

        return True

    def insert_books() -> bool:
        sql = f"""INSERT INTO {BOOKS_TABLE_NAME} (
            Isbn, Title
        ) VALUES (
            ?, ?
        );"""

        book_data = [tuple(row) for row in books[1:]]

        return try_insert(sql, book_data)

    def insert_book_authors() -> bool:
        # TODO: shouldn't ignore... there is an issue with the normalize code
        sql = f"""INSERT OR IGNORE INTO {BOOK_AUTHORS_TABLE_NAME} (
            Author_id, Isbn
        ) VALUES (
            ?, ?
        );"""

        book_authors_data = [tuple(row) for row in book_authors[1:]]

        return try_insert(sql, book_authors_data)

    def insert_authors() -> bool:
        sql = f"""INSERT INTO {AUTHORS_TABLE_NAME} (
            Author_id, Name
        ) VALUES (
            ?, ?
        );"""

        authors_data = [tuple(row) for row in authors[1:]]

        return try_insert(sql, authors_data)

    def insert_borrowers() -> bool:
        sql = f"""INSERT INTO {BORROWERS_TABLE_NAME} (
            Ssn, Bname, Address, Phone
        ) VALUES (
            ?, ?, ?, ?
        );"""

        borrowers_data = [tuple(row[1:]) for row in borrowers]

        return try_insert(sql, borrowers_data)

    insert_successes = [insert_books(),
                        insert_book_authors(),
                        insert_authors(),
                        insert_borrowers()]

    conn.close()

    return all(insert_successes)

