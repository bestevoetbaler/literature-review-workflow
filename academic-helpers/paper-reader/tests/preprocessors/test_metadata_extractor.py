import os
from preprocessors.metadata_extractor import MetadataExtractor


def test_extract_from_filename():
    """Test metadata extraction from filename pattern."""
    extractor = MetadataExtractor()

    # Test filename pattern: Author_Year_Title.pdf
    metadata = extractor.extract_from_filename(
        "Turner_2018_Food_Environment_Framework.pdf"
    )

    assert 'Turner' in metadata['authors']
    assert metadata['year'] == 2018
    assert 'Food Environment Framework' in metadata['title']
    assert metadata['extraction_source'] == 'filename'


def test_extract_metadata_returns_structure():
    """Test that extract returns required metadata structure."""
    extractor = MetadataExtractor()

    # Mock extraction (we'll test with real PDF later)
    metadata = extractor._create_empty_metadata()

    required_keys = ['title', 'authors', 'year', 'journal', 'doi',
                     'abstract', 'keywords', 'extraction_source', 'confidence']

    for key in required_keys:
        assert key in metadata
