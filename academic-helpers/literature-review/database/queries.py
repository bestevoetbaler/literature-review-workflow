# database/queries.py
"""Database query layer for literature review."""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

class ReviewDatabase:
    """Database operations for literature reviews."""

    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize with database connection.

        Args:
            connection: SQLite connection
        """
        self.conn = connection

    def create_review(
        self,
        review_name: str,
        research_question: str,
        inclusion_criteria_json: str,
        reviewers_json: str,
        search_strategy: Optional[str] = None,
        use_ai_suggestions: bool = True
    ) -> int:
        """
        Create a new review project.

        Returns:
            review_id of created review
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (
                review_name,
                research_question,
                inclusion_criteria_json,
                reviewers_json,
                search_strategy,
                use_ai_suggestions
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            review_name,
            research_question,
            inclusion_criteria_json,
            reviewers_json,
            search_strategy,
            use_ai_suggestions
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_review(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Get review by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM reviews WHERE review_id = ?
        """, (review_id,))

        row = cursor.fetchone()
        if row is None:
            return None

        return dict(row)

    def link_paper_to_review(self, review_id: int, paper_id: str) -> None:
        """Link a paper from central library to this review."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO review_papers (review_id, paper_id)
            VALUES (?, ?)
        """, (review_id, paper_id))
        self.conn.commit()

    def get_review_papers(self, review_id: int) -> List[str]:
        """Get all paper IDs linked to this review."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT paper_id FROM review_papers
            WHERE review_id = ?
            ORDER BY date_added
        """, (review_id,))

        return [row[0] for row in cursor.fetchall()]

    def insert_screening(
        self,
        review_id: int,
        paper_id: str,
        reviewer_id: str,
        stage: str,
        decision: str,
        rationale: Optional[str] = None
    ) -> int:
        """Record a screening decision."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO paper_screening (
                review_id,
                paper_id,
                reviewer_id,
                stage,
                decision,
                rationale
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (review_id, paper_id, reviewer_id, stage, decision, rationale))
        self.conn.commit()
        return cursor.lastrowid

    def get_screening_decisions(
        self,
        review_id: int,
        paper_id: str,
        stage: str
    ) -> List[Dict[str, Any]]:
        """Get all screening decisions for a paper at a stage."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM paper_screening
            WHERE review_id = ? AND paper_id = ? AND stage = ?
            ORDER BY timestamp
        """, (review_id, paper_id, stage))

        return [dict(row) for row in cursor.fetchall()]

    def insert_extraction(
        self,
        review_id: int,
        paper_id: str,
        reviewer_id: str,
        template_name: str,
        extracted_data_json: str
    ) -> int:
        """Save extraction data."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO paper_extraction (
                review_id,
                paper_id,
                reviewer_id,
                template_name,
                extracted_data_json
            ) VALUES (?, ?, ?, ?, ?)
        """, (review_id, paper_id, reviewer_id, template_name, extracted_data_json))
        self.conn.commit()
        return cursor.lastrowid

    def get_extractions(
        self,
        review_id: int,
        paper_id: str
    ) -> List[Dict[str, Any]]:
        """Get all extractions for a paper."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM paper_extraction
            WHERE review_id = ? AND paper_id = ?
            ORDER BY timestamp
        """, (review_id, paper_id))

        return [dict(row) for row in cursor.fetchall()]

    def insert_theme(
        self,
        review_id: int,
        theme_name: str,
        created_by: str,
        theme_description: Optional[str] = None,
        parent_theme_id: Optional[int] = None
    ) -> int:
        """Create a new theme."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO themes (
                review_id,
                theme_name,
                theme_description,
                parent_theme_id,
                created_by
            ) VALUES (?, ?, ?, ?, ?)
        """, (review_id, theme_name, theme_description, parent_theme_id, created_by))
        self.conn.commit()
        return cursor.lastrowid

    def get_themes(self, review_id: int) -> List[Dict[str, Any]]:
        """Get all themes for a review."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM themes
            WHERE review_id = ?
            ORDER BY timestamp
        """, (review_id,))

        return [dict(row) for row in cursor.fetchall()]
