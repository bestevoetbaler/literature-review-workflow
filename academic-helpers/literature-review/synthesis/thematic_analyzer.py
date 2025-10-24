# synthesis/thematic_analyzer.py
"""AI-assisted thematic synthesis."""
import json
from typing import Dict, List, Any, Optional
from collections import Counter
import re
from database.queries import ReviewDatabase

class ThematicSynthesizer:
    """Thematic synthesis with optional AI assistance."""

    def __init__(self, review_db: ReviewDatabase, use_ai: bool = True):
        """
        Initialize thematic synthesizer.

        Args:
            review_db: ReviewDatabase instance
            use_ai: Whether to use AI for theme suggestions
        """
        self.review_db = review_db
        self.use_ai = use_ai

        if use_ai:
            try:
                from sentence_transformers import SentenceTransformer
                from sklearn.cluster import DBSCAN
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                self.DBSCAN = DBSCAN
            except ImportError:
                self.use_ai = False
                self.embedder = None
                self.DBSCAN = None

    @staticmethod
    def _check_ai_dependencies() -> bool:
        """Check if AI dependencies are available."""
        try:
            import sentence_transformers
            import sklearn
            return True
        except ImportError:
            return False

    def suggest_themes(
        self,
        review_id: int,
        field_name: str = 'main_results'
    ) -> Dict[str, Any]:
        """
        Suggest themes from extracted data.

        Args:
            review_id: Review ID
            field_name: Extraction field to analyze

        Returns:
            Dictionary with suggested themes or raw extractions
        """
        # Get all extractions for this review
        extractions = self._get_all_extractions_field(review_id, field_name)

        if not self.use_ai or self.embedder is None:
            # Manual mode - return raw data
            return {
                'mode': 'manual',
                'extractions': extractions
            }

        # Extract text values
        texts = []
        paper_ids = []

        for extraction in extractions:
            data = json.loads(extraction['extracted_data_json'])
            value = data.get(field_name)

            if isinstance(value, list):
                for item in value:
                    texts.append(str(item))
                    paper_ids.append(extraction['paper_id'])
            elif value:
                texts.append(str(value))
                paper_ids.append(extraction['paper_id'])

        if not texts:
            return {
                'mode': 'ai',
                'themes': [],
                'note': 'No text to cluster'
            }

        # Embed all findings
        embeddings = self.embedder.encode(texts)

        # Cluster similar findings
        clusterer = self.DBSCAN(eps=0.5, min_samples=2, metric='cosine')
        clusters = clusterer.fit_predict(embeddings)

        # Generate theme suggestions
        suggested_themes = []
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Noise cluster
                continue

            # Get texts in this cluster
            cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
            cluster_texts = [texts[i] for i in cluster_indices]
            cluster_papers = [paper_ids[i] for i in cluster_indices]

            # Extract keywords for theme name
            theme_name = self._extract_keywords(cluster_texts)

            suggested_themes.append({
                'suggested_name': theme_name,
                'example_quotes': cluster_texts[:5],
                'paper_ids': list(set(cluster_papers)),
                'paper_count': len(set(cluster_papers)),
                'finding_count': len(cluster_texts)
            })

        # Sort by paper count
        suggested_themes.sort(key=lambda t: t['paper_count'], reverse=True)

        return {
            'mode': 'ai',
            'themes': suggested_themes,
            'total_findings': len(texts),
            'clustered_findings': sum(1 for c in clusters if c != -1),
            'unclustered_findings': sum(1 for c in clusters if c == -1)
        }

    def _get_all_extractions_field(
        self,
        review_id: int,
        field_name: str
    ) -> List[Dict[str, Any]]:
        """Get all extractions with specified field."""
        # Get all papers in review
        papers = self.review_db.get_review_papers(review_id)

        extractions = []
        for paper_id in papers:
            paper_extractions = self.review_db.get_extractions(review_id, paper_id)

            for extraction in paper_extractions:
                data = json.loads(extraction['extracted_data_json'])
                if field_name in data:
                    extractions.append(extraction)

        return extractions

    def _extract_keywords(self, texts: List[str]) -> str:
        """Extract common keywords from cluster texts."""
        # Tokenize and count words
        words = []
        for text in texts:
            # Remove punctuation, lowercase, split
            tokens = re.findall(r'\b[a-z]{4,}\b', text.lower())
            words.extend(tokens)

        # Get most common words
        common_words = Counter(words).most_common(3)

        # Create theme name
        theme_name = ' + '.join(word for word, count in common_words)
        return theme_name.title()
