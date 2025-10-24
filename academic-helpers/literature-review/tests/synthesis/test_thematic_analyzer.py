# tests/synthesis/test_thematic_analyzer.py
import pytest
import json
from synthesis.thematic_analyzer import ThematicSynthesizer
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

@pytest.fixture
def synthesizer(db):
    """Create thematic synthesizer."""
    return ThematicSynthesizer(db, use_ai=False)  # Disable AI for unit tests

def test_suggest_themes_manual_mode(synthesizer, db):
    """Test theme suggestion in manual mode."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    # Add some extractions
    db.insert_extraction(
        review_id, 'paper_001', 'reviewer_A', 'observational_study',
        json.dumps({'main_results': ['Food deserts limit access']})
    )

    result = synthesizer.suggest_themes(review_id, field_name='main_results')

    assert result['mode'] == 'manual'
    assert 'extractions' in result

@pytest.mark.skipif(
    not ThematicSynthesizer._check_ai_dependencies(),
    reason="AI dependencies not available"
)
def test_suggest_themes_ai_mode(db):
    """Test AI theme suggestion."""
    synthesizer = ThematicSynthesizer(db, use_ai=True)
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    # Add similar extractions
    db.insert_extraction(
        review_id, 'paper_001', 'reviewer_A', 'observational_study',
        json.dumps({'main_results': ['Food deserts limit access', 'Transportation barriers']})
    )
    db.insert_extraction(
        review_id, 'paper_002', 'reviewer_A', 'observational_study',
        json.dumps({'main_results': ['Distance to stores', 'Car ownership low']})
    )

    result = synthesizer.suggest_themes(review_id, field_name='main_results')

    assert result['mode'] == 'ai'
    assert 'themes' in result
    assert len(result['themes']) > 0
