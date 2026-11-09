import html
import csv
from typing import Optional

from database.dtypes import CSVData, StringMatrix
import database as db

import random
import sqlite3
from datetime import date, timedelta
from database.names import BOOK_LOANS_TABLE_NAME

def from_csv() -> Optional[CSVData]:

    books_data = _read_books()
    borrowers_data = _read_borrowers()

    if not (books_data and borrowers_data):
        return None

    (books, book_authors, authors) = books_data
    borrowers = borrowers_data

    return (books, book_authors, authors, borrowers)

def _read_borrowers() -> Optional[StringMatrix]:
    borrowers_result: StringMatrix = []

    try:
        with open('data/borrower.csv', encoding='utf-8') as file:
            rows = list(csv.reader(file))

            for row in rows[1:]:
                row = [html.unescape(field) for field in row]

                [idn, ssn, fname, lname, _, addr, city, state, phone] = row
                full_name = f'{fname} {lname}'
                address = f'{addr}, {city}, {state}'

                new_borrower = [int(idn[2:]), ssn, full_name, address, phone]
                borrowers_result.append(new_borrower)

    except FileNotFoundError:
        return None

    return sorted(borrowers_result, key=lambda x: x[0])

def _read_books() -> Optional[tuple[StringMatrix, StringMatrix, StringMatrix]]:
    books_data: StringMatrix = []
    authors_data: StringMatrix = []
    book_authors_data: StringMatrix = []

    try:
        with open('data/book.csv', encoding='utf-8') as file:
            rows = list(csv.reader(file, delimiter='\t'))

            author_id_incr = 0
            author_set = {}

            for row in rows[1:]:
                row = [html.unescape(field) for field in row]

                [isbn10, _, title, authors, _, _, _] = row

                new_book = [isbn10, title]
                books_data.append(new_book)

                for author in authors.split(','):
                    author = author.strip()

                    if author == '':
                        author = 'Unknown Author'

                    if author not in author_set:
                        author_set[author] = author_id_incr
                        author_id_incr += 1

                    new_book_author = [author_set[author], isbn10]
                    book_authors_data.append(new_book_author)

            for (name, author_id) in author_set.items():
                new_author = [author_id, name]
                authors_data.append(new_author)

    except FileNotFoundError:
        return None

    return (books_data, book_authors_data, authors_data)


def load_additional_test_data(db_name: str) -> bool:
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        
        c.execute("SELECT Isbn FROM BOOK")
        all_isbns = [row[0] for row in c.fetchall()]
        
        if not all_isbns:
            conn.close()

            return False
        
        loans_data = []
        today = date.today()
        
        num_loans = random.randint(200, 500)
        
        for _ in range(num_loans):
            card_id = random.randint(1, 1000)
            isbn = random.choice(all_isbns)
            
            days_ago = random.randint(0, 90)
            date_out = today - timedelta(days=days_ago)
            
            due_date = date_out + timedelta(days=14)
            
            is_returned = random.random() < 0.7 # pct chance
            
            if is_returned:
                max_days_to_return = (today - date_out).days
                days_to_return = random.randint(10, max(10, max_days_to_return))
                date_in = date_out + timedelta(days=days_to_return)
                
                if date_in > today:
                    date_in = today
                
                loans_data.append((
                    isbn,
                    card_id,
                    date_out.isoformat(),
                    due_date.isoformat(),
                    date_in.isoformat()
                ))
            else:
                loans_data.append((
                    isbn,
                    card_id,
                    date_out.isoformat(),
                    due_date.isoformat(),
                    None
                ))
        
        sql = f"""
        INSERT INTO {BOOK_LOANS_TABLE_NAME} (
            Isbn,
            Card_id,
            Date_out,
            Due_date,
            Date_in
        ) VALUES (?, ?, ?, ?, ?)
        """
        
        c.executemany(sql, loans_data)
        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print(f"Error loading test data: {e}")
        if conn:
            conn.rollback()
            conn.close()

        return False

    if not db.get_current_date():
        db.set_current_date(date.today())
    
    db.update_fines()

    return True
