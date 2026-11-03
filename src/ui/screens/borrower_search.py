from typing import Optional

from textual.widgets import Input

from ui.screens import SearchScreen
from ui.modals import BorrowerDetailModal

from models import BorrowerSearchResult

import database as db

class BorrowerSearchScreen(SearchScreen):

    def __init__(self):
        def borrower_search(query: str, filters: Optional[dict]) -> list[BorrowerSearchResult]:
            return db.search_borrowers(query)

        super().__init__(
            title="Borrower Search",
            columns=[
                ("Card ID", 12),
                ("Name", 50),
                ("Checkouts", 9),
                ("Fines", 9),
            ],
            search_fn=borrower_search,
            detail_modal=BorrowerDetailModal,
            placeholder="Search Name or ID...",
            on_detail_callback=self.handle_response,
            filters={
                'columns': [('Card ID', True), ('Name', True)],
            }
        )

    def get_detail_data(self, row_data: tuple) -> BorrowerSearchResult:
        return row_data

    def get_key(self, data: BorrowerSearchResult) -> int:
        return data.id

    def handle_response(self, new_query: str | None) -> None:
        input_box = self.query_one(Input)

        if new_query:
            input_box.value = new_query
            self.handle_search(input_box.value)
        else:
            self.handle_search(input_box.value)
