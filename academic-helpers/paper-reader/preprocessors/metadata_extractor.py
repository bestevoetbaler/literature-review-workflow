import re
from typing import Dict, List, Any, Optional


class MetadataExtractor:
    """Extract metadata from PDF files using multiple strategies."""

    def __init__(self):
        """Initialize metadata extractor."""
        pass

    def extract_from_filename(self, filename: str) -> Dict[str, Any]:
        """
        Extract metadata from filename pattern.

        Common patterns:
        - Author_Year_Title.pdf
        - Author et al Year Title.pdf
        - Year Author Title.pdf

        Args:
            filename: PDF filename

        Returns:
            Metadata dictionary
        """
        metadata = self._create_empty_metadata()
        metadata['extraction_source'] = 'filename'

        # Remove .pdf extension
        name = filename.replace('.pdf', '').replace('_', ' ')

        # Pattern: Author_Year_Title
        # Look for 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', name)
        if year_match:
            year = int(year_match.group(0))
            metadata['year'] = year

            # Text before year is likely author
            before_year = name[:year_match.start()].strip()
            if before_year:
                # Take first word as author surname
                author = before_year.split()[0]
                metadata['authors'] = [author]

            # Text after year is likely title
            after_year = name[year_match.end():].strip()
            if after_year:
                metadata['title'] = after_year

        # Set confidence based on what we extracted
        extracted_fields = sum([
            bool(metadata['title']),
            bool(metadata['authors']),
            bool(metadata['year'])
        ])
        metadata['confidence'] = extracted_fields / 3.0

        return metadata

    def _create_empty_metadata(self) -> Dict[str, Any]:
        """Create empty metadata structure."""
        return {
            'title': '',
            'authors': [],
            'year': None,
            'journal': '',
            'volume': '',
            'issue': '',
            'pages': '',
            'doi': '',
            'abstract': '',
            'keywords': [],
            'extraction_source': 'unknown',
            'confidence': 0.0
        }
