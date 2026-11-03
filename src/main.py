#!/usr/bin/env python3

import argparse
from pathlib import Path

import database as db

from app import app

project_root = Path(__file__)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Library Management System.")
    parser.add_argument('-i', '--init', action='store_true', help='Specify to initialize the DB on startup.')
    parser.add_argument('-r', '--resettime', action='store_true', help='Reset the time info for some reason.')
    parser.add_argument('-f', '--force', action='store_true', help='Force commands to execute (eg. force a re-init of the db).')
    parser.add_argument('-l', '--library', help='Pass a specific filename to be used for the database.')
    parser.add_argument('-t', '--testdata', help='Loads /additonal/ test data into the database if init is also passed.')
    # parser.add_argument('-v', '--verbose', help='Show logs.')
    args = parser.parse_args()

    db_name = str(project_root / "library.db")

    if args.library:
        db_name = str(project_root / args.library)

    db_exists = db.exists(db_name)

    if args.resettime:
        if db_exists:
            print("Resetting time info to today.")
            db.config.set_db_name(db_name)
            db.reset_time()
        else:
            print("You must first initialize a database.")
            print("  Hint: Use the '--init' command line flag.")
            exit(1)

    if args.init:
        if db_exists:
            if args.force:
                print(f"Deleting the database at '{db_name}'.")
                db.delete(db_name)
            else:
                print(f"A database already exists at '{db_name}'. Either:")
                print("- Remove the init command line flag to use this database,")
                print(f"- Delete/Rename the file at '{db_name}', or")
                print("- Pass the force flag to override this error.")
                exit(1)

        print("Initializing the database.")
        db_exists = db.init(db_name)

        if db_exists:
            print(f"Database created and initialized at '{db_name}'.")
        else:
            print(f"Failed to initialize the database at '{db_name}'.")
            exit(1)

        if args.testdata:
            print("Loading additional data for testing.")
            db.load_additional_test_data(db_name)

    if not db_exists:
        print("You must first initialize a database.")
        print("  Hint: Use the '--init' command line flag.")
        exit(1)

    app.run()

if __name__ == '__main__':
    main()
