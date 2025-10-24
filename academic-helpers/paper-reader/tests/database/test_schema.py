import sqlite3
from database.connection import get_database_connection


def test_papers_table_exists():
    """Test that papers table is created."""
    conn = get_database_connection(':memory:')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='papers'
    """)

    result = cursor.fetchone()
    assert result is not None
    assert result[0] == 'papers'
    conn.close()


def test_papers_table_structure():
    """Test papers table has required columns."""
    conn = get_database_connection(':memory:')
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(papers)")
    columns = {row[1] for row in cursor.fetchall()}

    required_columns = {'paper_id', 'file_path', 'title', 'authors_json',
                       'year', 'doi', 'abstract'}
    assert required_columns.issubset(columns)
    conn.close()


def test_fts_table_exists():
    """Test that FTS5 virtual table is created."""
    conn = get_database_connection(':memory:')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='papers_fts'
    """)

    result = cursor.fetchone()
    assert result is not None
    conn.close()
