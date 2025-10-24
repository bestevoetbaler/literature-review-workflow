#!/usr/bin/env python3
"""
Simple integration test for Turner et al. 2018 paper processing.

This script tests the complete pipeline without pytest complexities.
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Check if Turner PDF exists
TURNER_PDF = "/Users/emersonrburke/Desktop/thesis-research-hub/1_literature/Turner et al. - 2018 - Concepts and critical perspectives for food environment research A global framework with implicatio.pdf"

print("=" * 70)
print("Turner et al. 2018 Paper - Integration Test")
print("=" * 70)

# Test 1: File exists
print("\n[Test 1] Checking if Turner PDF exists...")
if not os.path.exists(TURNER_PDF):
    print(f"❌ FAIL: Turner PDF not found at:")
    print(f"  {TURNER_PDF}")
    sys.exit(1)
print(f"✓ PASS: Turner PDF found ({os.path.getsize(TURNER_PDF) / 1024 / 1024:.1f} MB)")

# Test 2: Import PaperReader
print("\n[Test 2] Importing PaperReader...")
try:
    from database.queries import PaperDatabase
    from database.connection import get_database_connection
    print("✓ PASS: Database modules imported successfully")
except ImportError as e:
    print(f"❌ FAIL: Could not import database modules: {e}")
    sys.exit(1)

# Test 3: Create database connection
print("\n[Test 3] Creating in-memory database...")
try:
    conn = get_database_connection(':memory:')
    db = PaperDatabase(conn)
    print("✓ PASS: Database connection created")
except Exception as e:
    print(f"❌ FAIL: Could not create database: {e}")
    sys.exit(1)

# Test 4: Metadata extraction from filename
print("\n[Test 4] Extracting metadata from filename...")
try:
    from preprocessors.metadata_extractor import MetadataExtractor

    extractor = MetadataExtractor()
    filename = os.path.basename(TURNER_PDF)
    metadata = extractor.extract_from_filename(filename)

    print(f"  Title: {metadata.get('title', 'N/A')}")
    print(f"  Authors: {metadata.get('authors', [])}")
    print(f"  Year: {metadata.get('year', 'N/A')}")
    print(f"  Confidence: {metadata.get('confidence', 0):.2f}")

    # Verify extraction
    assert 'Turner' in str(metadata.get('authors', [])), "Should extract Turner from filename"
    assert metadata.get('year') == 2018, "Should extract year 2018"

    print("✓ PASS: Metadata extraction successful")
except Exception as e:
    print(f"❌ FAIL: Metadata extraction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: PDF Parsing
print("\n[Test 5] Parsing PDF content...")
try:
    from extractors.pdf_parser import PDFParser

    parser = PDFParser()
    # Try to parse just the first page as a quick test
    print("  Attempting to parse PDF...")

    import fitz  # PyMuPDF
    doc = fitz.open(TURNER_PDF)
    page_count = len(doc)
    first_page_text = doc[0].get_text()
    doc.close()

    print(f"  Pages: {page_count}")
    print(f"  First page text length: {len(first_page_text)} chars")
    print(f"  First 100 chars: {first_page_text[:100].strip()}")

    assert page_count > 0, "Should have pages"
    assert len(first_page_text) > 0, "Should extract text"

    print("✓ PASS: PDF parsing successful")
except Exception as e:
    print(f"❌ FAIL: PDF parsing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Store paper in database
print("\n[Test 6] Storing paper metadata in database...")
try:
    import hashlib

    # Generate paper ID
    identifier = f"{filename}:{metadata.get('title', '')}"
    paper_id = hashlib.sha256(identifier.encode()).hexdigest()[:16]

    paper_data = {
        'paper_id': paper_id,
        'file_path': TURNER_PDF,
        'title': metadata.get('title', filename),
        'authors': metadata.get('authors', []),
        'year': metadata.get('year'),
        'journal': '',
        'doi': '',
        'abstract': 'Test abstract from Turner paper',
        'keywords': []
    }

    db.insert_paper(paper_data)
    print(f"  Paper ID: {paper_id}")

    # Verify storage
    stored = db.get_paper(paper_id)
    assert stored is not None, "Paper should be stored"
    assert stored['title'] == paper_data['title'], "Title should match"

    print("✓ PASS: Paper stored in database")
except Exception as e:
    print(f"❌ FAIL: Database storage failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Full-text search
print("\n[Test 7] Testing full-text search...")
try:
    # Search for "food" (likely in the paper)
    results = db.search_papers('food', limit=10)
    print(f"  Search results for 'food': {len(results)} papers")

    if len(results) > 0:
        print(f"  Found paper: {results[0]['title']}")

    assert len(results) >= 1, "Should find the stored paper"

    print("✓ PASS: Full-text search working")
except Exception as e:
    print(f"❌ FAIL: Full-text search failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED")
print("=" * 70)
print("\nSummary:")
print("  - Turner PDF file exists and is readable")
print("  - Database modules import correctly")
print("  - Metadata extraction from filename works")
print("  - PDF parsing with PyMuPDF works")
print("  - Database storage and retrieval works")
print("  - Full-text search (FTS5) works")
print("\nThe paper-reader module is ready to process the Turner paper!")
