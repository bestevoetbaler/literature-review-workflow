# tests/database/test_queries.py
import pytest
import json
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database for testing."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

def test_create_review(db):
    """Test creating a new review."""
    review_id = db.create_review(
        review_name='Test Review',
        research_question='What is the impact?',
        inclusion_criteria_json=json.dumps({'criteria': 'test'}),
        reviewers_json=json.dumps(['reviewer_A', 'reviewer_B'])
    )

    assert review_id is not None
    assert isinstance(review_id, int)

def test_get_review(db):
    """Test retrieving a review."""
    review_id = db.create_review(
        review_name='Test Review',
        research_question='What is the impact?',
        inclusion_criteria_json=json.dumps({'criteria': 'test'}),
        reviewers_json=json.dumps(['reviewer_A'])
    )

    review = db.get_review(review_id)

    assert review is not None
    assert review['review_name'] == 'Test Review'
    assert review['research_question'] == 'What is the impact?'

def test_link_paper_to_review(db):
    """Test linking a paper to a review."""
    review_id = db.create_review(
        review_name='Test',
        research_question='Question?',
        inclusion_criteria_json='{}',
        reviewers_json='[]'
    )

    db.link_paper_to_review(review_id, 'paper_001')

    papers = db.get_review_papers(review_id)
    assert len(papers) == 1
    assert papers[0] == 'paper_001'
