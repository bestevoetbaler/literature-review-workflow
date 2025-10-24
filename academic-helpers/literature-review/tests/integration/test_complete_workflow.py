"""Integration test for complete literature review workflow."""
import pytest
import json
from database.connection import get_database_connection
from database.queries import ReviewDatabase
from screening.interface import ScreeningInterface
from quality.reliability import ReliabilityCalculator
from extraction.template_loader import TemplateLoader

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

def test_complete_workflow(db):
    """Test complete literature review workflow."""

    # Step 1: Create review
    review_id = db.create_review(
        review_name='Food Environment Review',
        research_question='What is the impact of food deserts on health?',
        inclusion_criteria_json=json.dumps({
            'population': 'Urban adults',
            'outcome': 'Diet quality or health outcomes'
        }),
        reviewers_json=json.dumps(['reviewer_A', 'reviewer_B'])
    )

    assert review_id is not None

    # Step 2: Import papers
    db.link_paper_to_review(review_id, 'paper_001')
    db.link_paper_to_review(review_id, 'paper_002')
    db.link_paper_to_review(review_id, 'paper_003')

    papers = db.get_review_papers(review_id)
    assert len(papers) == 3

    # Step 3: Title/Abstract Screening - Dual independent
    screener = ScreeningInterface(db)

    # Reviewer A screens
    screener.record_decision(review_id, 'paper_001', 'reviewer_A', 'title_abstract', 'include')
    screener.record_decision(review_id, 'paper_002', 'reviewer_A', 'title_abstract', 'exclude', 'Wrong population')
    screener.record_decision(review_id, 'paper_003', 'reviewer_A', 'title_abstract', 'include')

    # Reviewer B screens
    screener.record_decision(review_id, 'paper_001', 'reviewer_B', 'title_abstract', 'include')
    screener.record_decision(review_id, 'paper_002', 'reviewer_B', 'title_abstract', 'exclude', 'Out of scope')
    screener.record_decision(review_id, 'paper_003', 'reviewer_B', 'title_abstract', 'include')

    # Step 4: Calculate screening reliability
    calculator = ReliabilityCalculator(db)
    kappa_result = calculator.calculate_screening_kappa(review_id, 'title_abstract')

    assert kappa_result['kappa'] == 1.0  # Perfect agreement
    assert kappa_result['interpretation'] == 'Almost Perfect'

    # Step 5: Data extraction for included papers
    loader = TemplateLoader()
    template = loader.load_template('observational_study')

    extraction_data = {
        'study_design': 'cross_sectional',
        'sample_size': 500,
        'population_description': 'Urban adults in food deserts',
        'exposure_variables': ['Distance to supermarket'],
        'outcome_variables': ['Diet quality score'],
        'main_results': ['Greater distance associated with lower diet quality'],
        'quality_score': 7
    }

    db.insert_extraction(
        review_id, 'paper_001', 'reviewer_A',
        'observational_study',
        json.dumps(extraction_data)
    )

    extractions = db.get_extractions(review_id, 'paper_001')
    assert len(extractions) == 1

    # Step 6: Thematic synthesis
    theme_id = db.insert_theme(
        review_id=review_id,
        theme_name='Geographic Barriers',
        theme_description='Physical distance limiting food access',
        created_by='reviewer_A'
    )

    assert theme_id is not None

    themes = db.get_themes(review_id)
    assert len(themes) == 1
    assert themes[0]['theme_name'] == 'Geographic Barriers'

    # Workflow complete
    review = db.get_review(review_id)
    assert review['status'] == 'active'
