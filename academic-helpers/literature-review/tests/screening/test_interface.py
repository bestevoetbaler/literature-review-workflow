# tests/screening/test_interface.py
import pytest
from screening.interface import ScreeningInterface
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

@pytest.fixture
def screener(db):
    """Create screening interface."""
    return ScreeningInterface(db)

def test_record_decision_include(screener, db):
    """Test recording include decision."""
    review_id = db.create_review(
        'Test Review',
        'Question?',
        '{}',
        '[]'
    )

    screener.record_decision(
        review_id=review_id,
        paper_id='paper_001',
        reviewer_id='reviewer_A',
        stage='title_abstract',
        decision='include'
    )

    decisions = db.get_screening_decisions(review_id, 'paper_001', 'title_abstract')
    assert len(decisions) == 1
    assert decisions[0]['decision'] == 'include'

def test_record_exclude_without_rationale_fails(screener, db):
    """Test that exclude decisions require rationale."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    with pytest.raises(ValueError, match="rationale"):
        screener.record_decision(
            review_id=review_id,
            paper_id='paper_001',
            reviewer_id='reviewer_A',
            stage='title_abstract',
            decision='exclude',
            rationale=None
        )

def test_record_exclude_with_rationale_succeeds(screener, db):
    """Test exclude with rationale works."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    screener.record_decision(
        review_id=review_id,
        paper_id='paper_001',
        reviewer_id='reviewer_A',
        stage='title_abstract',
        decision='exclude',
        rationale='Not in scope'
    )

    decisions = db.get_screening_decisions(review_id, 'paper_001', 'title_abstract')
    assert decisions[0]['rationale'] == 'Not in scope'
