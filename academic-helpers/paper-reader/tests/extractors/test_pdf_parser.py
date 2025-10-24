from extractors.pdf_parser import PDFParser


def test_parser_initialization():
    """Test PDFParser can be initialized."""
    parser = PDFParser()
    assert parser is not None


def test_parse_returns_document_object():
    """Test that parse returns a document structure."""
    parser = PDFParser()

    # Mock document (we'll test with real PDF in integration test)
    doc = parser._create_empty_document()

    assert 'text' in doc
    assert 'pages' in doc
    assert 'page_count' in doc
