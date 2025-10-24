import sqlite3
import json
from typing import Dict, List, Any, Optional


class PaperDatabase:
    """Database operations for paper storage and retrieval."""

    def __init__(self, connection: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = connection

    def insert_paper(self, paper_data: Dict[str, Any]) -> str:
        """
        Insert paper into database.

        Args:
            paper_data: Dictionary with paper metadata

        Returns:
            paper_id of inserted paper
        """
        cursor = self.conn.cursor()

        # Convert lists to JSON
        authors_json = json.dumps(paper_data.get('authors', []))
        keywords_json = json.dumps(paper_data.get('keywords', []))

        cursor.execute("""
            INSERT INTO papers (
                paper_id, file_path, title, authors_json, year,
                journal, volume, issue, pages, doi, abstract, keywords_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_data['paper_id'],
            paper_data['file_path'],
            paper_data.get('title', ''),
            authors_json,
            paper_data.get('year'),
            paper_data.get('journal', ''),
            paper_data.get('volume', ''),
            paper_data.get('issue', ''),
            paper_data.get('pages', ''),
            paper_data.get('doi', ''),
            paper_data.get('abstract', ''),
            keywords_json
        ))

        self.conn.commit()
        return paper_data['paper_id']

    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper by ID.

        Args:
            paper_id: Paper ID

        Returns:
            Paper dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def search_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text search across papers.

        Args:
            query: Search query (FTS5 syntax)
            limit: Maximum number of results

        Returns:
            List of matching papers
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT p.*
            FROM papers p
            WHERE p.paper_id IN (
                SELECT paper_id FROM papers_fts WHERE papers_fts MATCH ?
            )
            LIMIT ?
        """, (query, limit))

        return [dict(row) for row in cursor.fetchall()]

    def add_to_collection(self, paper_id: str, collection_name: str) -> None:
        """
        Add paper to a collection.

        Args:
            paper_id: Paper ID
            collection_name: Collection name
        """
        cursor = self.conn.cursor()

        # Create collection if it doesn't exist
        cursor.execute("""
            INSERT OR IGNORE INTO collections (name)
            VALUES (?)
        """, (collection_name,))

        # Get collection ID
        cursor.execute(
            "SELECT collection_id FROM collections WHERE name = ?",
            (collection_name,)
        )
        collection_id = cursor.fetchone()[0]

        # Add paper to collection
        cursor.execute("""
            INSERT OR IGNORE INTO paper_collections (paper_id, collection_id)
            VALUES (?, ?)
        """, (paper_id, collection_id))

        self.conn.commit()

    def get_papers_in_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Get all papers in a collection.

        Args:
            collection_name: Collection name

        Returns:
            List of papers
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT p.*
            FROM papers p
            JOIN paper_collections pc ON p.paper_id = pc.paper_id
            JOIN collections c ON pc.collection_id = c.collection_id
            WHERE c.name = ?
        """, (collection_name,))

        return [dict(row) for row in cursor.fetchall()]

    def insert_section(self, paper_id: str, section_name: str, content: str) -> int:
        """
        Insert section content for a paper.

        Args:
            paper_id: Paper ID
            section_name: Section name
            content: Section text content

        Returns:
            section_id
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO sections (paper_id, section_name, content, word_count)
            VALUES (?, ?, ?, ?)
        """, (paper_id, section_name, content, len(content.split())))

        self.conn.commit()
        return cursor.lastrowid
