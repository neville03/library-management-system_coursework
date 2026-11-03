from typing import Optional

from textual.widgets import Input, Button

from ui.screens import SearchScreen
from ui.modals import BookDetailModal

from models import BookSearchResult

import database as db

class BookSearchScreen(SearchScreen):

    def __init__(self):
        def book_search(query: str, filters: Optional[dict]) -> list[BookSearchResult]:
            return db.search_books(query, filters)

        super().__init__(
            title="Book Search",
            columns=[
                ("ISBN", 12),
                ("Title", 50),
                ("Authors", 25),
                ("Status", 12),
                ("Borrower ID", 12),
            ],
            search_fn=book_search,
            detail_modal=BookDetailModal,
            placeholder="Search by ISBN, title, or author...",
            on_detail_callback=self.handle_response,
            filters={
                'columns': [('ISBN', True), ('Title', True), ('Authors', True)],
                'availability': 'All',
            },
            filter_modal = (
                Button("Filter", id="filter-btn", variant="primary")
            )
        )

    def get_detail_data(self, row_data: BookSearchResult) -> BookSearchResult:
        return row_data

    def get_key(self, data: BookSearchResult) -> str:
        return data.isbn

    def handle_response(self, new_query: str | None) -> None:
        input_box = self.query_one(Input)

        if new_query:
            input_box.value = new_query
            self.handle_search(input_box.value)
        else:
            self.handle_search(input_box.value)
