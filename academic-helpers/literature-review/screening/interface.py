# screening/interface.py
"""Screening interface for literature review."""
from typing import Optional, Dict, Any
from database.queries import ReviewDatabase

class ScreeningInterface:
    """Interface for paper screening workflow."""

    def __init__(self, review_db: ReviewDatabase):
        """
        Initialize screening interface.

        Args:
            review_db: ReviewDatabase instance
        """
        self.review_db = review_db

    def record_decision(
        self,
        review_id: int,
        paper_id: str,
        reviewer_id: str,
        stage: str,
        decision: str,
        rationale: Optional[str] = None
    ) -> int:
        """
        Record a screening decision.

        Args:
            review_id: Review ID
            paper_id: Paper ID
            reviewer_id: Reviewer ID
            stage: Screening stage ('title_abstract', 'full_text', 'quality')
            decision: Decision ('include', 'exclude', 'maybe')
            rationale: Rationale for decision (required for 'exclude')

        Returns:
            screening_id

        Raises:
            ValueError: If exclude decision lacks rationale
        """
        # Validate exclude decisions have rationale
        if decision == 'exclude' and not rationale:
            raise ValueError(
                "Exclude decisions require rationale referencing inclusion criteria"
            )

        # Record decision
        screening_id = self.review_db.insert_screening(
            review_id=review_id,
            paper_id=paper_id,
            reviewer_id=reviewer_id,
            stage=stage,
            decision=decision,
            rationale=rationale
        )

        return screening_id

    def get_papers_needing_screening(
        self,
        review_id: int,
        reviewer_id: str,
        stage: str
    ) -> list:
        """
        Get papers that need screening by this reviewer at this stage.

        Args:
            review_id: Review ID
            reviewer_id: Reviewer ID
            stage: Screening stage

        Returns:
            List of paper IDs needing screening
        """
        # Get all papers in review
        all_papers = self.review_db.get_review_papers(review_id)

        # Filter to papers not yet screened by this reviewer
        needing_screening = []
        for paper_id in all_papers:
            decisions = self.review_db.get_screening_decisions(
                review_id,
                paper_id,
                stage
            )

            # Check if this reviewer has already screened
            reviewer_screened = any(
                d['reviewer_id'] == reviewer_id
                for d in decisions
            )

            if not reviewer_screened:
                needing_screening.append(paper_id)

        return needing_screening
