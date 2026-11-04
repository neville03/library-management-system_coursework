
from datetime import date
from models.result import BorrowerSearchResult
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TabbedContent, TabPane, DataTable, Static, SelectionList

from ui.custom import BaseModal

import database as db

class BorrowerDetailModal(BaseModal):

    def __init__(self, borrower_result: BorrowerSearchResult) -> None:
        super().__init__()

        self.borrower_data = db.get_borrower_by_id(borrower_result.id)

        self.active_checkouts = []
        self.all_checkouts = []

        if self.borrower_data:
            self.active_checkouts = db.get_loans_by_borrower_id(self.borrower_data.id, returned=False)
            self.all_checkouts = db.get_loans_by_borrower_id(self.borrower_data.id, returned=True)

            self.fines = db.get_fines_by_borrower_id(self.borrower_data.id)
            self.total_fines = db.get_total_fines_by_borrower_id(self.borrower_data.id)

    def on_mount(self) -> None:
        checkouts_table = self.query_one("#checkouts-history", DataTable)

        checkouts_table.zebra_stripes = True

        self.checkout_lookup = {}
        checkouts_table.add_columns(*["Loan ID", "ISBN", "Date Out", "In"])
        for loan in self.all_checkouts:
            checkouts_table.add_row(loan.id, loan.isbn, loan.date_out, loan.date_in, key=str(loan.id))
            self.checkout_lookup[loan.id] = loan

        if self.fines:
            fine_table = self.query_one("#fines-table", DataTable)

            fine_table.zebra_stripes = True

            fine_table.add_columns(*["Loan ID", "ISBN", "Days Overdue", "Amount"])
            for fine in self.fines:
                fine_table.add_row(
                    fine.loan_id,
                    fine.isbn,
                    ((fine.date_in or db.get_current_date() or date.today()) - fine.due_date).days,
                    fine.amt_dollars
                )

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Borrower Details", id="modal-title")

            with Vertical(classes="form-content"):
                if not self.borrower_data:
                    yield Label(f"Unable to access borrower data")
                else:
                    with TabbedContent():
                        with TabPane("Info"):
                            with Vertical():
                                yield Label(f"Card ID: {self.borrower_data.id}", classes="detail-line")
                                yield Label(f"Full Name: {self.borrower_data.name}", classes="detail-line")
                                yield Label(f"SSN: {self.borrower_data.ssn}", classes="detail-line")
                                yield Label(f"Address: {self.borrower_data.address}", classes="detail-line")
                                yield Label(f"Phone: {self.borrower_data.phone}", classes="detail-line")

                        with TabPane("Manage"):
                            with Vertical():
                                with Vertical(classes="input-field"):
                                    if not self.active_checkouts:
                                        yield Label("No Checkouts")
                                    else:
                                        yield Label("Active Checkouts")

                                        yield SelectionList[int](
                                            *[(
                                                f"[{loan.isbn}] {loan.title}",
                                                loan.id,
                                                bool(loan.date_in)
                                            ) for loan in self.active_checkouts],
                                            compact=True,
                                            id="searched-columns"
                                        )

                                        yield Button("Check-in Books", id="checkin-button", variant="primary")

                                    if not self.fines:
                                        yield Label("No Fines")
                                    else:
                                        yield Label("Fines")

                                        yield DataTable(id="fines-table")

                                        yield Label(f"Total: ${self.total_fines / 100:,.2f} owed")
                                        yield Button("Pay", id="pay-button", variant="primary")

                        with TabPane("Checkout History"):
                            with Vertical():
                                yield DataTable(id="checkouts-history")
                                yield Static("", id="result-count")

                with Horizontal(classes="form-buttons"):
                    yield Button("Close", id="close-button", variant="primary")

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'close-button':
            self.dismiss()

        elif event.button.id == 'checkin-button':
            selection_list = self.query_one(SelectionList)

            selected_items = [
                self.checkout_lookup[idx] for idx in selection_list.selected
            ]

            if selected_items:
                result = db.checkin_many(selected_items)

                if result.status:
                    self.notify(result.message, severity="information")
                    self.dismiss()
                else:
                    self.notify(result.message, severity="error")
            else:
                self.notify("You must make a selection.", severity="warning")

        elif event.button.id == 'pay-button':
            if self.borrower_data:
                result = db.pay_fines(self.borrower_data.id, self.total_fines)

                if result.status:
                    self.notify(result.message, severity="information")
                    self.dismiss()
                else:
                    self.notify(result.message, severity="error")
