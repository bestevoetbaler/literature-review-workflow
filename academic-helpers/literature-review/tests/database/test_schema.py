# tests/database/test_schema.py
import pytest
import sqlite3
from database.connection import get_database_connection

def test_reviews_table_exists():
    """Test that reviews table is created."""
    conn = get_database_connection(':memory:')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='reviews'
    """)

    result = cursor.fetchone()
    assert result is not None
    assert result[0] == 'reviews'

    conn.close()

def test_reviews_table_structure():
    """Test reviews table has required columns."""
    conn = get_database_connection(':memory:')
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(reviews)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    assert 'review_id' in columns
    assert 'review_name' in columns
    assert 'research_question' in columns
    assert 'inclusion_criteria_json' in columns
    assert columns['review_id'] == 'INTEGER'

    conn.close()
