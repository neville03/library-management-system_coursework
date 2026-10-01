from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

import database as db

class Author(BaseModel):
    id: int = Field(alias='Author_id')
    name: str = Field(alias='Name')

    model_config = ConfigDict(populate_by_name=True)

class Book(BaseModel):
    isbn: str = Field(alias='Isbn')
    title: str = Field(alias='Title')

class BookAuthor(BaseModel):
    author_id: int = Field(alias='Author_id')
    isbn: str = Field(alias='Isbn')

class Borrower(BaseModel):
    id: int = Field(alias='Card_id')
    ssn: str = Field(alias='Ssn')
    name: str = Field(alias='Bname')
    address: str = Field(alias='Address')
    phone: str = Field(alias='Phone')

class Loan(BaseModel):
    id: int = Field(alias='Loan_id')
    isbn: str = Field(alias='Isbn')
    borrower_id: int = Field(alias='Card_id')
    title: str = Field(alias='Title')
    date_out: date = Field(alias='Date_out')
    due_date: date = Field(alias='Due_date')
    date_in: Optional[date] = Field(alias='Date_in')

    def is_overdue_on(self, today: date) -> bool:
        return self.date_in is None and today > self.due_date

    @property
    def is_overdue(self) -> bool:
        not_returned = (self.date_in is None)
        past_due = (db.get_current_date() > self.due_date)

        return not_returned and past_due

class Fine(BaseModel):
    loan_id: int = Field(alias='Loan_id')
    amt: int = Field(alias='Fine_amt') # in cents
    paid: bool = Field(alias='Paid')