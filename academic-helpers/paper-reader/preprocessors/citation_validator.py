"""
Citation validation and duplicate detection using CrossRef API.

This module validates citations against CrossRef database and detects
duplicate papers using DOI matching and fuzzy title similarity.
"""

import time
import re
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher
import requests

from academic_helpers.paper_reader.config import get_config
from academic_helpers.paper_reader.utils import (
    get_logger,
    CrossRefAPIError,
    DuplicatePaperError,
    validate_doi,
    normalize_doi,
)


logger = get_logger(__name__)


class CitationValidator:
    """
    Validate citations using CrossRef API and detect duplicates.

    Features:
    - DOI-based validation (HIGH confidence)
    - Fuzzy title matching (MEDIUM/LOW confidence)
    - Duplicate detection by DOI and title similarity
    - Rate limiting for CrossRef API compliance
    """

    # Confidence levels
    CONFIDENCE_HIGH = 'HIGH'    # DOI match
    CONFIDENCE_MEDIUM = 'MEDIUM'  # Title match >80%
    CONFIDENCE_LOW = 'LOW'      # Title match <80%

    def __init__(self):
        """Initialize citation validator with configuration."""
        self.config = get_config()
        self._crossref_session = requests.Session()
        self._crossref_session.headers.update(self.config.get_crossref_headers())
        self._last_request_time = 0
        self._min_request_interval = 1.0 / 50.0  # 50 requests/second max

    def validate(self, references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate list of references against CrossRef database.

        Args:
            references: List of reference dictionaries with fields:
                - title: Citation title (required)
                - authors: List of author names (optional)
                - year: Publication year (optional)
                - doi: DOI if available (optional)

        Returns:
            List of validated citations with confidence levels and canonical metadata
        """
        logger.info(f"Validating {len(references)} citations...")

        validated_citations = []

        for i, ref in enumerate(references, 1):
            try:
                logger.debug(f"Validating citation {i}/{len(references)}")

                # Validate citation
                validated = self._validate_single_citation(ref)
                validated_citations.append(validated)

                # Rate limiting
                self._apply_rate_limit()

            except Exception as e:
                logger.warning(f"Failed to validate citation {i}: {e}")
                # Add citation with low confidence
                validated_citations.append({
                    'original': ref,
                    'validated': ref,
                    'confidence': self.CONFIDENCE_LOW,
                    'validation_error': str(e),
                })

        logger.info(f"Validation complete: {len(validated_citations)} citations processed")
        return validated_citations

    def check_duplicate(
        self,
        paper_metadata: Dict[str, Any],
        existing_papers: List[Dict[str, Any]]
    ) -> Optional[Tuple[str, float]]:
        """
        Check if paper is duplicate of existing papers.

        Args:
            paper_metadata: Metadata of paper to check (with title, doi)
            existing_papers: List of existing paper metadata dictionaries

        Returns:
            Tuple of (paper_id, similarity_score) if duplicate found, None otherwise
        """
        # Check DOI match first (exact duplicate)
        if paper_metadata.get('doi'):
            doi = normalize_doi(paper_metadata['doi'])
            for existing in existing_papers:
                if existing.get('doi'):
                    existing_doi = normalize_doi(existing['doi'])
                    if doi == existing_doi:
                        logger.info(f"Duplicate found by DOI: {doi}")
                        return (existing.get('paper_id'), 1.0)

        # Check title similarity
        if paper_metadata.get('title'):
            title = paper_metadata['title'].lower().strip()

            for existing in existing_papers:
                if existing.get('title'):
                    existing_title = existing['title'].lower().strip()
                    similarity = self._calculate_title_similarity(title, existing_title)

                    if similarity >= self.config.DUPLICATE_TITLE_THRESHOLD:
                        logger.info(f"Duplicate found by title similarity: {similarity:.2%}")
                        return (existing.get('paper_id'), similarity)

        return None

    def _validate_single_citation(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single citation.

        Args:
            reference: Citation dictionary

        Returns:
            Validated citation with confidence level
        """
        # If DOI present, validate via CrossRef
        if reference.get('doi'):
            doi = normalize_doi(reference['doi'])
            if validate_doi(doi):
                return self._validate_by_doi(reference, doi)

        # No DOI, try fuzzy title match
        if reference.get('title'):
            return self._validate_by_title(reference)

        # Cannot validate
        return {
            'original': reference,
            'validated': reference,
            'confidence': self.CONFIDENCE_LOW,
            'validation_method': 'none',
        }

    def _validate_by_doi(self, reference: Dict[str, Any], doi: str) -> Dict[str, Any]:
        """
        Validate citation using DOI lookup in CrossRef.

        Args:
            reference: Original citation
            doi: Normalized DOI

        Returns:
            Validated citation with HIGH confidence
        """
        try:
            # Query CrossRef for canonical metadata
            url = f"{self.config.CROSSREF_API_BASE}/works/{doi}"
            response = self._crossref_session.get(url, timeout=10)

            if response.status_code == 404:
                logger.warning(f"DOI not found in CrossRef: {doi}")
                return {
                    'original': reference,
                    'validated': reference,
                    'confidence': self.CONFIDENCE_LOW,
                    'validation_method': 'doi_not_found',
                }

            response.raise_for_status()
            data = response.json()

            if 'message' not in data:
                raise CrossRefAPIError("Invalid CrossRef response")

            # Extract canonical metadata
            canonical = self._extract_crossref_metadata(data['message'])

            return {
                'original': reference,
                'validated': canonical,
                'confidence': self.CONFIDENCE_HIGH,
                'validation_method': 'doi',
                'doi': doi,
            }

        except requests.RequestException as e:
            logger.warning(f"CrossRef API error for DOI {doi}: {e}")
            return {
                'original': reference,
                'validated': reference,
                'confidence': self.CONFIDENCE_LOW,
                'validation_method': 'doi_api_error',
            }

    def _validate_by_title(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate citation using fuzzy title matching against CrossRef.

        Args:
            reference: Original citation with title

        Returns:
            Validated citation with MEDIUM/LOW confidence
        """
        title = reference['title'].strip()

        try:
            # Query CrossRef by title
            url = f"{self.config.CROSSREF_API_BASE}/works"
            params = {
                'query.title': title,
                'rows': 5,  # Top 5 matches
            }

            response = self._crossref_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'message' not in data or 'items' not in data['message']:
                raise CrossRefAPIError("Invalid CrossRef response")

            items = data['message']['items']

            if not items:
                # No matches found
                return {
                    'original': reference,
                    'validated': reference,
                    'confidence': self.CONFIDENCE_LOW,
                    'validation_method': 'title_no_match',
                }

            # Find best match using title similarity
            best_match = None
            best_similarity = 0.0

            for item in items:
                if 'title' in item and item['title']:
                    crossref_title = item['title'][0].lower().strip()
                    similarity = self._calculate_title_similarity(
                        title.lower(),
                        crossref_title
                    )

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = item

            # Determine confidence based on similarity
            if best_similarity >= 0.8:
                confidence = self.CONFIDENCE_MEDIUM
            else:
                confidence = self.CONFIDENCE_LOW

            # Extract metadata from best match
            validated = self._extract_crossref_metadata(best_match) if best_match else reference

            return {
                'original': reference,
                'validated': validated,
                'confidence': confidence,
                'validation_method': 'title_fuzzy',
                'title_similarity': best_similarity,
            }

        except requests.RequestException as e:
            logger.warning(f"CrossRef API error for title '{title}': {e}")
            return {
                'original': reference,
                'validated': reference,
                'confidence': self.CONFIDENCE_LOW,
                'validation_method': 'title_api_error',
            }

    def _extract_crossref_metadata(self, crossref_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract standard metadata from CrossRef API response.

        Args:
            crossref_data: CrossRef 'message' object

        Returns:
            Dictionary with citation metadata
        """
        metadata = {}

        # Title
        if 'title' in crossref_data and crossref_data['title']:
            metadata['title'] = crossref_data['title'][0]

        # Authors
        if 'author' in crossref_data:
            authors = []
            for author in crossref_data['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    authors.append(f"{family}, {given}".strip(', '))
            metadata['authors'] = authors

        # Year
        if 'published' in crossref_data:
            date_parts = crossref_data['published'].get('date-parts', [[]])
            if date_parts and date_parts[0]:
                metadata['year'] = date_parts[0][0]

        # Journal
        if 'container-title' in crossref_data and crossref_data['container-title']:
            metadata['journal'] = crossref_data['container-title'][0]

        # Volume, issue, pages
        if 'volume' in crossref_data:
            metadata['volume'] = crossref_data['volume']

        if 'issue' in crossref_data:
            metadata['issue'] = crossref_data['issue']

        if 'page' in crossref_data:
            metadata['pages'] = crossref_data['page']

        # DOI
        if 'DOI' in crossref_data:
            metadata['doi'] = normalize_doi(crossref_data['DOI'])

        return metadata

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using Levenshtein distance.

        Args:
            title1: First title (normalized)
            title2: Second title (normalized)

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize titles (remove punctuation, extra spaces)
        def normalize(text: str) -> str:
            # Remove punctuation
            text = re.sub(r'[^\w\s]', '', text)
            # Remove extra whitespace
            text = ' '.join(text.split())
            return text.lower()

        norm1 = normalize(title1)
        norm2 = normalize(title2)

        # Calculate sequence matcher ratio
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        return similarity

    def _apply_rate_limit(self):
        """
        Apply rate limiting for CrossRef API (max 50 requests/second).
        """
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            time.sleep(sleep_time)

        self._last_request_time = time.time()
