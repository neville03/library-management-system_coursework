from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.validation import Length
from textual.widgets import Label, Button, TabbedContent, TabPane, DataTable, Static, Input

from models.result import BookSearchResult

from ui.components import Tag

import database as db

from ui.custom import BaseModal

class BookDetailModal(BaseModal):

    def __init__(self, book_result: BookSearchResult) -> None:
        super().__init__()

        self.book_data = book_result

        if self.book_data.borrower_id:
            self.borrower_data = db.get_borrower_by_id(self.book_data.borrower_id)

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Book Details", id="modal-title")

            with Vertical(classes="form-content"):
                with TabbedContent():
                    with TabPane("Info"):
                        with Vertical():
                            yield Label(f"ISBN: {self.book_data.isbn}", classes="detail-line")
                            yield Label(f"Title: {self.book_data.title}", classes="detail-line")

                            with Horizontal(classes="detail-line"):
                                yield Label("Authors: ")
                                for author in self.book_data.authors:
                                    yield Tag(author)

                            yield Label(f"Status: {self.book_data.status_display}", classes="detail-line")
                            if self.book_data.borrower_id and self.borrower_data:
                                yield Label(
                                    f"Borrower: {self.borrower_data.name} (ID: {self.borrower_data.id})",
                                    classes="detail-line"
                                )

                    with TabPane("Manage"):
                        with Vertical():
                            if self.book_data.status:
                                with Vertical(classes="input-field"):
                                    yield Label("Checkout Book")
                                    with Horizontal(classes='side-by-side'):
                                        yield Input(
                                            placeholder="Enter a Borrower ID...",
                                            type="text",
                                            validators=[
                                                Length(minimum=1)
                                            ]
                                        )

                                        yield Button("Check-Out Book", id="checkout-button", variant="primary")

                            else:
                                if self.borrower_data:
                                    yield Label(f"Borrower: {self.borrower_data.name} (ID: {self.borrower_data.id})", classes="detail-line")

                                    loan = None
                                    if self.book_data.borrower_id:
                                        loan = db.get_loans_by_borrower_id(self.borrower_data.id)[0]

                                    if loan:
                                        yield Label(f"Loan ID: {loan.id}", classes="detail-line")
                                        yield Label(f"Loaned On: {loan.date_out}", classes="detail-line")
                                        yield Label(f"Due: {loan.due_date}", classes="detail-line")

                                    yield Button("Check-In Book", id="checkin-button", variant="primary")

                    with TabPane("Checkout History"):
                        with Vertical():
                            yield DataTable()
                            yield Static("", id="result-count")

            with Horizontal(classes="form-buttons"):
               yield Button("Close", id="close-button", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)

        table.add_column("Loan ID", width=8)
        table.add_column("Borrower ID", width=12)
        table.add_column("Date Out", width=12)
        table.add_column("Date In", width=12)

        book_loans = db.get_loans_by_isbn(self.book_data.isbn, returned=True)

        if book_loans:
            for loan in book_loans:
                table.add_row(loan.id, loan.borrower_id, loan.date_out, loan.date_in)

        self.update_result_count()

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'close-button':
            self.dismiss()

        elif event.button.id == 'checkout-button':
            input_box = self.query_one(Input)

            try:
                result = db.create_loan(self.book_data.isbn, int(input_box.value))
            except ValueError:
                self.notify("You must provide a number.", severity="error")
                return

            if result.status:
                self.notify(result.message, severity="information")
                self.dismiss()
            else:
                self.notify(result.message, severity="error")

        elif event.button.id == 'checkin-button':
            loan = None

            if self.book_data.borrower_id:
                loan = db.get_loans_by_borrower_id(self.book_data.borrower_id)[0]

            if loan:
                result = db.checkin(loan.id)

                if result.status:
                    self.notify(result.message, severity="information")
                    self.dismiss()
                else:
                    self.notify(result.message, severity="error")

    @on(Tag.Clicked)
    def handle_tag_clicked(self, event: Tag.Clicked) -> None:
        self.dismiss(event.title)

    def update_result_count(self) -> None:
        table = self.query_one(DataTable)
        count = table.row_count

        item_count = self.query_one("#result-count", Static)
        item_count.update(f"{count} results found")
