import pytest
from quality.reliability import ReliabilityCalculator
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

@pytest.fixture
def calculator(db):
    """Create reliability calculator."""
    return ReliabilityCalculator(db)

def test_calculate_kappa_perfect_agreement(calculator, db):
    """Test kappa calculation with perfect agreement."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')
    db.link_paper_to_review(review_id, 'paper_001')
    db.link_paper_to_review(review_id, 'paper_002')

    # Both reviewers agree on both papers
    db.insert_screening(review_id, 'paper_001', 'reviewer_A', 'title_abstract', 'include')
    db.insert_screening(review_id, 'paper_001', 'reviewer_B', 'title_abstract', 'include')
    db.insert_screening(review_id, 'paper_002', 'reviewer_A', 'title_abstract', 'exclude', 'Out of scope')
    db.insert_screening(review_id, 'paper_002', 'reviewer_B', 'title_abstract', 'exclude', 'Out of scope')

    result = calculator.calculate_screening_kappa(review_id, 'title_abstract')

    assert result['kappa'] == 1.0
    assert result['interpretation'] == 'Almost Perfect'
    assert result['percent_agreement'] == 100.0

def test_calculate_kappa_no_agreement(calculator, db):
    """Test kappa with complete disagreement."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')
    db.link_paper_to_review(review_id, 'paper_001')
    db.link_paper_to_review(review_id, 'paper_002')

    # Reviewers disagree on both papers
    db.insert_screening(review_id, 'paper_001', 'reviewer_A', 'title_abstract', 'include')
    db.insert_screening(review_id, 'paper_001', 'reviewer_B', 'title_abstract', 'exclude', 'Bad')
    db.insert_screening(review_id, 'paper_002', 'reviewer_A', 'title_abstract', 'exclude', 'Bad')
    db.insert_screening(review_id, 'paper_002', 'reviewer_B', 'title_abstract', 'include')

    result = calculator.calculate_screening_kappa(review_id, 'title_abstract')

    assert result['kappa'] < 0.2
    assert result['percent_agreement'] == 0.0
