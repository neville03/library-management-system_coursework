from textual.app import  ComposeResult
from textual.containers import Horizontal, Vertical, Grid, Container
from textual.widgets import Input, Button, Label, Static

from database import config
from ui.custom import BaseModal

import database as db

class SettingsModal(BaseModal):
    CSS = """

    SettingsModal #button-grid {
        grid-size: 2 2;
        grid-gutter: 1;
        width: 100%;
        height: auto;
        margin-top: 1;
    }

    SettingsModal #button-grid Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Settings", id="modal-title")

            with Vertical(classes="form-content"):
                with Vertical(classes="input-field"):
                    yield Label("Change Database File")
                    with Horizontal(classes="side-by-side"):
                        yield Input(placeholder="library.db", id="db-input")
                        yield Button("Change", id="change-db-button")

                with Vertical(classes="input-field"):
                    with Grid(id="button-grid"):
                        yield Button("Init database", id="init-db-button")
                        yield Button("Re-Init database", id="reinit-db-button")
                        yield Button("Reset time", id="reset-time-button")
                        yield Button("Load Extra Data", id="load-data-button")

                with Horizontal(classes="form-buttons"):
                    yield Button("Close", id="close-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "change-db-button":
            input_box = self.query_one("#db-input", Input)

            if input_box.value:
                config.set_db_name(input_box.value)

                self.notify("Database file changed!", severity="information")
                self.notify("Unless a database already exists at this location, you must initialize it.", severity="warning")

            else:
                self.notify("You must pass a filename!", severity="error")

        elif event.button.id == "init-db-button":
            db_exists = db.exists(config.db_name)

            if not db_exists:
                success = db.init(config.db_name)

                if success:
                    self.notify("Database initialized successfully!", severity="information")
                    self.dismiss()
                else:
                    self.notify("Database failed to initialize!", severity="error")

            else:
                self.notify(f"Database already exists at {config.db_name}!", severity="error")

        elif event.button.id == "reinit-db-button":
            if db.delete(config.db_name):
                success = db.init(config.db_name)

                if success:
                    self.notify("Database re-initialized successfully!", severity="information")
                    self.dismiss()
                else:
                    self.notify("Database failed to re-initialize!", severity="error")

            else:
                self.notify(f"Unable to delete old database at {config.db_name}!", severity="error")

        elif event.button.id == "reset-time-button":
            success = db.reset_time()

            if success:
                self.notify("Time reset successfully!", severity="information")
                self.dismiss()
            else:
                self.notify("Unable to reset the databse time!", severity="error")

        elif event.button.id == "load-data-button":
            success = db.load_additional_test_data(config.db_name)

            if success:
                self.notify("Additional test data loaded!", severity="information")
                self.dismiss()
            else:
                self.notify("Unable to load additional test data!", severity="error")

        elif event.button.id == "close-button":
            if db.exists(config.db_name) and db.is_initialized():
                self.dismiss()
            else:
                self.notify("You must initialize the database first!", severity="error")
