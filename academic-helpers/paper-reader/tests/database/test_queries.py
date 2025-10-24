import json
from database.connection import get_database_connection
from database.queries import PaperDatabase


def test_insert_paper():
    """Test inserting a paper into database."""
    conn = get_database_connection(':memory:')
    db = PaperDatabase(conn)

    paper_data = {
        'paper_id': 'test_001',
        'file_path': '/path/to/paper.pdf',
        'title': 'Test Paper',
        'authors': ['Author One', 'Author Two'],
        'year': 2020,
        'abstract': 'This is a test abstract.'
    }

    db.insert_paper(paper_data)

    # Verify paper was inserted
    paper = db.get_paper('test_001')
    assert paper is not None
    assert paper['title'] == 'Test Paper'
    assert paper['year'] == 2020
    conn.close()


def test_search_papers_fts():
    """Test full-text search functionality."""
    conn = get_database_connection(':memory:')
    db = PaperDatabase(conn)

    # Insert test papers with unique DOIs (empty string for no DOI)
    db.insert_paper({
        'paper_id': 'p1',
        'file_path': '/path/p1.pdf',
        'title': 'Urban Food Systems',
        'authors': ['Smith'],
        'year': 2020,
        'abstract': 'Study of urban food deserts.',
        'doi': '10.1000/test1'
    })

    db.insert_paper({
        'paper_id': 'p2',
        'file_path': '/path/p2.pdf',
        'title': 'Rural Agriculture',
        'authors': ['Jones'],
        'year': 2021,
        'abstract': 'Study of rural farming practices.',
        'doi': '10.1000/test2'
    })

    # Search for "urban"
    results = db.search_papers('urban', limit=10)

    assert len(results) == 1
    assert results[0]['paper_id'] == 'p1'
    conn.close()


def test_add_to_collection():
    """Test adding paper to collection."""
    conn = get_database_connection(':memory:')
    db = PaperDatabase(conn)

    # Insert paper
    db.insert_paper({
        'paper_id': 'p1',
        'file_path': '/path/p1.pdf',
        'title': 'Test Paper',
        'authors': ['Smith'],
        'year': 2020,
        'abstract': 'Abstract'
    })

    # Create collection and add paper
    db.add_to_collection('p1', 'food_systems')

    # Verify paper is in collection
    papers = db.get_papers_in_collection('food_systems')
    assert len(papers) == 1
    assert papers[0]['paper_id'] == 'p1'
    conn.close()
