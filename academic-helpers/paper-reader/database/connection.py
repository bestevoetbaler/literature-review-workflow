import sqlite3
import os


def get_database_connection(db_path=None):
    """
    Get database connection with schema initialized.

    Args:
        db_path: Path to database file. If None, uses default.
                 Use ':memory:' for in-memory database.

    Returns:
        sqlite3.Connection
    """
    if db_path is None:
        db_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'papers.db'
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name

    # Initialize schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())

    return conn
